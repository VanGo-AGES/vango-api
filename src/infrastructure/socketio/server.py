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

# sid_meta: socket_id → { "trip_id": str, "role": "tracker" | "follower", "user_id": str }
sid_meta: dict[str, dict] = {}


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


# US10-TK04 / US10-TK08
@sio.event
async def location_update(sid: str, data: dict) -> None:  # type: ignore[empty-body]
    pass


# US11-TK04
async def emit_trip_finished(trip_id: str) -> None:
    """Emite trip_finished para todos no room da sessão e remove o estado em memória.

    Chamado pelo TripService após finalizar a viagem.
    Silenciosamente ignorado se não houver sessão ativa para o trip_id.
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
