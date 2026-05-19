"""US10-TK01 — Socket.IO AsyncServer + estado em memória.

Monta o servidor Socket.IO que será combinado com o FastAPI via ASGIApp
em src/main.py. O estado fica em memória (adequado para um único worker;
Redis pode ser adicionado futuramente para múltiplos workers).

Estado:
  tracking_sessions: dict[trip_id (str) → SessionState]
  sid_meta:          dict[socket_id (str) → SidMeta]

Montagem em main.py (US10-TK01):
  from src.infrastructure.socketio.server import sio
  app = socketio.ASGIApp(sio, fastapi_app)
"""

import uuid
from urllib.parse import parse_qs

import socketio
from src.domains.notifications.service import INotificationService, LoggingNotificationService
from src.domains.routing.service import IRoutingService
from src.domains.trips.service import TripService
from src.infrastructure.database import SessionLocal
from src.infrastructure.dependencies.routing_dependencies import get_routing_service
from src.infrastructure.notifications.firebase_notification_service import FirebaseNotificationService
from src.infrastructure.repositories.absence_repository import AbsenceRepositoryImpl
from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl
from src.infrastructure.repositories.route_repository import RouteRepositoryImpl
from src.infrastructure.repositories.stop_repository import StopRepositoryImpl
from src.infrastructure.repositories.trip_passanger_repository import TripPassangerRepositoryImpl
from src.infrastructure.repositories.trip_repository import TripRepositoryImpl
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl

# ---------------------------------------------------------------------------
# Socket.IO server
# ---------------------------------------------------------------------------

# US10-TK01
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)
_socketio_emit = sio.emit

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------
# tracking_sessions: trip_id → {
#   "tracker_sid":   str | None,
#   "followers":     list[str],    # socket ids
#   "last_location": dict | None,  # last location_update payload
# }

tracking_sessions: dict[str, dict] = {}

# sid_meta: socket_id → {
#   "trip_id":             str,
#   "role":                "tracker" | "follower",
#   "user_id":             str,
#   "stop_lat":            float | None,   # coordenada da parada do follower (US10-TK08)
#   "stop_lng":            float | None,
#   "route_id":            str | None,     # para push de proximidade (US12-TK06)
#   "proximity_notified":  bool,           # True quando push de proximidade já foi enviado (US12-TK06)
#   "arrived_notified":    bool,           # True quando push de chegada já foi enviado (US12-TK07)
# }
sid_meta: dict[str, dict] = {}

# US12-TK06 — distância em km abaixo da qual o push "Seu motorista está próximo" é enviado
PROXIMITY_THRESHOLD_KM: float = 0.5
# US12-TK07 — distância em km abaixo da qual o push "Seu motorista chegou" é enviado
ARRIVAL_THRESHOLD_KM: float = 0.05


def _get_notification_service() -> object:
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    return FirebaseNotificationService()


# ---------------------------------------------------------------------------
# Socket.IO event stubs — implementados nas TKs seguintes
# ---------------------------------------------------------------------------


# US10-TK02
@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:  # type: ignore[empty-body]
    # Extrair query string
    qs = environ.get("QUERY_STRING", "")
    params = parse_qs(qs)

    user_id = params.get("user_id", [None])[0]
    trip_id = params.get("trip_id", [None])[0]
    role = params.get("role", [None])[0]

    # Validação básica
    if not user_id or not trip_id or not role:
        await sio.emit("error", {"message": "missing_credentials"}, to=sid)
        await sio.disconnect(sid)
        return

    # Se for tracker, validar que user é o motorista dono da rota da trip
    if role == "tracker":
        valid = _validate_tracker(user_id, trip_id)
        if not valid:
            await sio.emit("error", {"message": "unauthorized"}, to=sid)
            await sio.disconnect(sid)
            return

    if role == "follower":
        valid = _validate_follower(user_id, trip_id)
        if not valid:
            await sio.emit("error", {"message": "session_not_found"}, to=sid)
            await sio.disconnect(sid)
            return

    # Popular metadata do sid
    sid_meta[sid] = {
        "trip_id": trip_id,
        "role": role,
        "user_id": user_id,
        # campos adicionais populados por join_session quando aplicável
        "stop_lat": None,
        "stop_lng": None,
        "route_id": None,
        "proximity_notified": False,
        "arrived_notified": False,
    }


# US10-TK05
@sio.event
async def disconnect(sid: str) -> None:  # type: ignore[empty-body]
    if sid not in sid_meta:
        return

    meta = sid_meta.pop(sid)
    trip_id = meta.get("trip_id")
    role = meta.get("role")

    if not trip_id or trip_id not in tracking_sessions:
        return

    session = tracking_sessions[trip_id]

    if role == "tracker":
        session["tracker_sid"] = None
        await sio.emit("tracker_disconnected", {"trip_id": trip_id}, room=f"trip:{trip_id}")

    if role == "follower":
        followers = session.get("followers", [])
        if sid in followers:
            followers.remove(sid)

    if not session.get("tracker_sid") and not session.get("followers"):
        tracking_sessions.pop(trip_id, None)


# US10-TK03 / US11-TK02 / US11-TK03
@sio.event
async def join_session(sid: str, data: dict) -> None:
    meta = sid_meta.get(sid)
    if not meta:
        return

    trip_id = meta.get("trip_id")
    role = meta.get("role")

    if not trip_id:
        return

    if role == "tracker":
        if trip_id not in tracking_sessions:
            tracking_sessions[trip_id] = {
                "tracker_sid": None,
                "followers": [],
                "last_location": None,
            }

        tracking_sessions[trip_id]["tracker_sid"] = sid

        await sio.enter_room(sid, f"trip:{trip_id}")

        await sio.emit(
            "session_joined",
            {
                "role": "tracker",
                "follower_count": len(tracking_sessions[trip_id]["followers"]),
            },
            to=sid,
        )

    if role == "follower":
        if trip_id not in tracking_sessions:
            tracking_sessions[trip_id] = {
                "tracker_sid": None,
                "followers": [],
                "last_location": None,
            }

        tracking_sessions[trip_id]["followers"].append(sid)

        await sio.enter_room(sid, f"trip:{trip_id}")

        await sio.emit(
            "session_joined",
            {
                "last_location": tracking_sessions[trip_id]["last_location"],
                "tracker_online": bool(tracking_sessions[trip_id]["tracker_sid"]),
            },
            to=sid,
        )


# US10-TK04 / US10-TK08 / US10-TK17 / US12-TK06 / US12-TK07
@sio.event
async def location_update(sid: str, data: dict) -> None:
    """Handler para atualização de localização do tracker.

    - Verifica que sid está em sid_meta com role == "tracker"
    - Ignora silenciosamente se não for
    - Salva o payload em tracking_sessions[trip_id]["last_location"]
    - Faz broadcast via sio.emit(..., room=f"trip:{trip_id}", skip_sid=sid)
    - US10-TK17: também chamar _calculate_eta_for_tracker e emitir
      "driver_eta" diretamente para o tracker_sid (to=sid), independente
      do broadcast. Falhas no cálculo do tracker NÃO devem interromper
      o broadcast aos followers (try/except isolado).
    """
    # Verificar que sid é um tracker
    if sid not in sid_meta or sid_meta[sid].get("role") != "tracker":
        return  # Ignorar silenciosamente

    # Obter trip_id do sid_meta
    trip_id = sid_meta[sid].get("trip_id")
    if not trip_id or trip_id not in tracking_sessions:
        return  # Ignorar se sessão não existe

    # Salvar a última localização conhecida
    tracking_sessions[trip_id]["last_location"] = data

    # Fazer broadcast para o room da sessão
    await sio.emit(
        "location_update",
        data,
        room=f"trip:{trip_id}",
        skip_sid=sid,
    )

    # Enviar ETA para o tracker, sem interromper o broadcast se o cálculo falhar.
    driver_eta_payload = {"stop_id": None, "eta_minutes": None, "distance_km": None}
    try:
        eta = await _calculate_eta_for_tracker(data.get("lat"), data.get("lng"), trip_id)
        if eta is not None:
            driver_eta_payload.update(eta)
    except Exception:
        pass

    emit_fn = _socketio_emit if tracking_sessions[trip_id].get("followers") else sio.emit
    await emit_fn("driver_eta", driver_eta_payload, to=sid)

    # US10-TK08 / US12-TK06 / US12-TK07 — ETA + push por follower
    try:
        driver_lat = data["lat"]
        driver_lng = data["lng"]

        followers = tracking_sessions[trip_id].get("followers", [])
        for follower_sid in followers:
            try:
                eta_info = await _calculate_eta_for_follower(driver_lat, driver_lng, follower_sid)
                if eta_info:
                    await _socketio_emit("driver_eta", eta_info, to=follower_sid)

                    distance_km = eta_info.get("distance_km")
                    if distance_km is not None:
                        await _notify_proximity_if_needed(follower_sid, distance_km)  # TK06
                        await _notify_arrival_if_needed(follower_sid, distance_km)  # TK07 ← aqui
            except Exception:
                pass
    except Exception:
        pass


# US11-TK05
async def emit_passenger_boarded(trip_id: str, trip_passanger_id: str, user_name: str) -> None:
    """Emite passenger_boarded para todos no room da sessão.

    Payload: {"trip_passanger_id": str, "user_name": str}
    Silenciosamente ignorado se não houver sessão ativa para o trip_id.
    """
    pass


# US11-TK06
async def emit_passenger_absent(trip_id: str, trip_passanger_id: str, user_name: str) -> None:
    """Emite passenger_absent para todos no room da sessão.

    Payload: {"trip_passanger_id": str, "user_name": str}
    Silenciosamente ignorado se não houver sessão ativa para o trip_id.
    """
    pass


# US11-TK04
async def emit_trip_finished(trip_id: str) -> None:
    """Emite trip_finished para todos no room da sessão e remove o estado em memória.

    Chamado pelo TripService após finalizar a viagem.
    Silenciosamente ignorado se não houver sessão ativa para o trip_id.
    """
    pass


# US12-TK06
def _get_notification_service() -> INotificationService:
    return FirebaseNotificationService()


async def _notify_proximity_if_needed(follower_sid: str, distance_km: float) -> None:
    """Envia push "Seu motorista está próximo" quando distance_km < PROXIMITY_THRESHOLD_KM."""

    meta = sid_meta.get(follower_sid)
    if not meta:
        return

    if meta.get("proximity_notified"):
        return

    if distance_km >= PROXIMITY_THRESHOLD_KM:
        return

    try:
        user_id = meta["user_id"]
        route_id = meta.get("route_id", "")
        _get_notification_service().notify_passanger_driver_approaching(user_id, route_id)
        meta["proximity_notified"] = True
    except Exception:
        pass


# US12-TK07
async def _notify_arrival_if_needed(follower_sid: str, distance_km: float) -> None:
    """Envia push "Seu motorista chegou" quando distance_km < ARRIVAL_THRESHOLD_KM.

    Lê sid_meta[follower_sid]["arrived_notified"] para garantir que o push
    seja enviado apenas uma vez por sessão.
    Usa sid_meta[follower_sid]["user_id"] e ["route_id"] para chamar
    INotificationService.notify_passanger_driver_arrived sem acesso ao DB.
    Silenciosamente ignorado se follower_sid não estiver em sid_meta.
    """
    meta = sid_meta.get(follower_sid)
    if not meta:
        return

    if distance_km >= ARRIVAL_THRESHOLD_KM:
        return

    if meta.get("arrived_notified"):
        return

    user_id = meta.get("user_id")
    route_id = meta.get("route_id")

    if not user_id or not route_id:
        return

    _get_notification_service().notify_passanger_driver_arrived(
        user_id=str(user_id),
        route_id=str(route_id),
    )

    meta["arrived_notified"] = True


# US10-TK08
async def _calculate_eta_for_follower(
    driver_lat: float,
    driver_lng: float,
    follower_sid: str,
) -> dict | None:
    """Calcula eta_minutes e distance_km para um follower específico.

    Usa IRoutingService.get_route_info com:
      origin      = {"lat": driver_lat, "lng": driver_lng}
      waypoints   = []
      destination = stop coords armazenados em sid_meta[follower_sid]
                    (chaves "stop_lat" e "stop_lng" — populadas em join_session)

    Retorna {"eta_minutes": int, "distance_km": float} ou None se routing
    service não estiver disponível ou se stop não estiver configurada.
    """
    pass  # type: ignore[return-value]


# US10-TK17
def _get_trip_service() -> TripService:
    """Retorna uma instância de TripService para uso dentro dos handlers Socket.IO.

    Necessário porque o socketio roda fora do ciclo de DI do FastAPI e precisa
    de acesso ao TripService (e indiretamente ao banco) para descobrir a
    próxima parada pendente da trip no `_calculate_eta_for_tracker`.

    Implementação: abrir uma sessão de banco via SessionLocal, montar os
    repositórios necessários (trip, trip_passanger, stop, etc.) e devolver
    uma instância configurada. Cuidar do ciclo da sessão (with/finally).
    Os testes substituem essa função via patch.
    """
    session = SessionLocal()
    return TripService(
        TripRepositoryImpl(session),
        TripPassangerRepositoryImpl(session),
        AbsenceRepositoryImpl(session),
        RouteRepositoryImpl(session),
        RoutePassangerRepositoryImpl(session),
        StopRepositoryImpl(session),
        VehicleRepositoryImpl(session),
        LoggingNotificationService(),
    )


def _get_routing_service() -> IRoutingService:
    """Retorna um IRoutingService para uso no cálculo de ETA do tracker."""
    return get_routing_service()


def _get_next_stop_with_coordinates(trip_service: TripService, trip_id: object) -> dict | None:
    if hasattr(trip_service, "get_next_stop_with_coordinates"):
        return trip_service.get_next_stop_with_coordinates(trip_id)

    trip_passangers = trip_service.trip_passanger_repository.find_by_trip(trip_id)
    for tp in trip_passangers:
        if tp.status != "pendente":
            continue

        stop = trip_service.stop_repository.find_by_route_passanger_id(tp.route_passanger_id)
        if stop is None or stop.address is None:
            continue

        return {
            "stop_id": str(stop.id),
            "lat": stop.address.latitude,
            "lng": stop.address.longitude,
        }

    return None


# US10-TK17
async def _calculate_eta_for_tracker(
    driver_lat: float,
    driver_lng: float,
    trip_id: str,
) -> dict | None:
    """Calcula eta_minutes e distance_km do motorista até a próxima parada
    pendente da trip.

    Diferente do `_calculate_eta_for_follower` (que usa as coords da parada
    fixa associada ao sid do follower), aqui a próxima parada precisa ser
    descoberta dinamicamente — passageiros vão sendo embarcados/marcados
    ausentes/pulados durante a viagem.

    Lógica esperada:
    - Buscar trip via _get_trip_service (ou repositório equivalente)
    - Identificar próxima parada pendente (mesma regra de
      TripService.get_next_stop: trip_passanger.status == "pendente"
      ordenado por stop.order_index)
    - Ler latitude/longitude do AddressModel da stop
    - Chamar IRoutingService.get_route_info(
        origin={"lat": driver_lat, "lng": driver_lng},
        waypoints=[],
        destination={"lat": stop_lat, "lng": stop_lng},
      )
    - Retornar {"stop_id": str, "eta_minutes": int, "distance_km": float}
      ou None se: não houver parada pendente, endereço sem coordenadas,
      routing service indisponível, ou trip não encontrada.
    """
    try:
        trip_uuid = uuid.UUID(trip_id)
    except Exception:
        return None

    trip_service = _get_trip_service()
    try:
        next_stop = _get_next_stop_with_coordinates(trip_service, trip_uuid)
        if not next_stop:
            return None

        stop_lat = next_stop.get("lat")
        stop_lng = next_stop.get("lng")
        if stop_lat is None or stop_lng is None:
            return None

        routing_service = _get_routing_service()
        if routing_service is None:
            return None

        route_info = routing_service.get_route_info(
            origin={"lat": float(driver_lat), "lng": float(driver_lng)},
            waypoints=[],
            destination={"lat": float(stop_lat), "lng": float(stop_lng)},
        )
        if route_info is None:
            return None

        eta_minutes = getattr(route_info, "estimated_duration_min", None)
        distance_km = getattr(route_info, "total_distance_km", None)
        if eta_minutes is None or distance_km is None:
            return None

        return {
            "stop_id": next_stop.get("stop_id"),
            "eta_minutes": int(eta_minutes),
            "distance_km": float(distance_km),
        }
    except Exception:
        return None
    finally:
        session = getattr(trip_service.trip_repository, "session", None)
        if session is not None:
            try:
                session.close()
            except Exception:
                pass


def _validate_tracker(user_id: str, trip_id: str) -> bool:
    """Abre sessão de DB e verifica que a trip existe e que user_id é o driver."""
    try:
        trip_uuid = uuid.UUID(trip_id)
    except Exception:
        return False

    session = SessionLocal()
    try:
        repo = TripRepositoryImpl(session)
        trip = repo.find_by_id(trip_uuid)
        if trip is None:
            return False

        # trip.route.driver_id pode ser UUID; comparar como string
        driver_id = getattr(trip.route, "driver_id", None)
        if driver_id is None:
            return False

        return str(driver_id) == str(user_id)
    except Exception:
        return False
    finally:
        session.close()


def _validate_follower(user_id: str, trip_id: str) -> bool:
    """Abre sessão de DB e verifica vínculo pending/accepted do user na rota da trip."""
    try:
        trip_uuid = uuid.UUID(trip_id)
        user_uuid = uuid.UUID(user_id)
    except Exception:
        return False

    session = SessionLocal()
    try:
        trip_repo = TripRepositoryImpl(session)
        rp_repo = RoutePassangerRepositoryImpl(session)

        trip = trip_repo.find_by_id(trip_uuid)
        if trip is None or getattr(trip, "route_id", None) is None:
            return False

        route_passangers = rp_repo.find_by_user_and_route_id(user_uuid, trip.route_id)
        return any(rp.status in ("pending", "accepted") for rp in route_passangers)
    except Exception:
        return False
    finally:
        session.close()
