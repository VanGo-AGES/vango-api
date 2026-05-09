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


# US10-TK04
@sio.event
async def location_update(sid: str, data: dict) -> None:  # type: ignore[empty-body]
    pass
