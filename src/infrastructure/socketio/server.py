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

import socketio

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


# ---------------------------------------------------------------------------
# Socket.IO event stubs — implementados nas TKs seguintes
# ---------------------------------------------------------------------------


# US10-TK02
@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:  # type: ignore[empty-body]
    pass


# US10-TK05
@sio.event
async def disconnect(sid: str) -> None:  # type: ignore[empty-body]
    pass


# US10-TK03 / US11-TK02 / US11-TK03
@sio.event
async def join_session(sid: str, data: dict) -> None:  # type: ignore[empty-body]
    pass


# US10-TK04 / US10-TK08 / US12-TK06 / US12-TK07
@sio.event
async def location_update(sid: str, data: dict) -> None:  # type: ignore[empty-body]
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
async def _notify_proximity_if_needed(follower_sid: str, distance_km: float) -> None:
    """Envia push "Seu motorista está próximo" quando distance_km < PROXIMITY_THRESHOLD_KM.

    Lê sid_meta[follower_sid]["proximity_notified"] para garantir que o push
    seja enviado apenas uma vez por sessão (não a cada location_update).
    Usa sid_meta[follower_sid]["user_id"] e ["route_id"] para chamar
    INotificationService.notify_passanger_driver_approaching sem acesso ao DB.
    Silenciosamente ignorado se follower_sid não estiver em sid_meta.
    """
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
    pass


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
