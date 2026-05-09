"""US10 / US11 — Testes do servidor Socket.IO.

Cada seção cobre uma TK:
  TK01 — servidor existe, estado inicializado, ASGIApp montável
  TK02 — autenticação connect (tracker)
  TK03 — join_session tracker + session_joined
  TK04 — location_update + broadcast
  TK05 — disconnect + tracker_disconnected + cleanup
  US11-TK02 — autenticação connect (follower, vínculo ativo)
  US11-TK03 — join_session follower + last_location
  US11-TK04 — trip_finished + TripService integration
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trip_id() -> str:
    return str(uuid.uuid4())


def _make_user_id() -> str:
    return str(uuid.uuid4())


# ===========================================================================
# US10-TK01 — servidor + ASGI + estado em memória
# ===========================================================================


@pytest.mark.skip(reason="US10-TK01")
def test_sio_server_is_async_server():
    """sio deve ser uma instância de socketio.AsyncServer."""
    import socketio as sio_lib

    from src.infrastructure.socketio.server import sio

    assert isinstance(sio, sio_lib.AsyncServer)


@pytest.mark.skip(reason="US10-TK01")
def test_tracking_sessions_starts_empty():
    """tracking_sessions deve iniciar como dict vazio."""
    from src.infrastructure.socketio.server import tracking_sessions

    assert isinstance(tracking_sessions, dict)


@pytest.mark.skip(reason="US10-TK01")
def test_sid_meta_starts_empty():
    """sid_meta deve iniciar como dict vazio."""
    from src.infrastructure.socketio.server import sid_meta

    assert isinstance(sid_meta, dict)


@pytest.mark.skip(reason="US10-TK01")
def test_asgi_app_mountable():
    """socketio.ASGIApp(sio, fastapi_app) deve ser criado sem erros."""
    import socketio as sio_lib

    from src.infrastructure.socketio.server import sio
    from src.main import app as fastapi_app

    combined = sio_lib.ASGIApp(sio, fastapi_app)
    assert combined is not None


# ===========================================================================
# US10-TK02 — autenticação de conexão (tracker)
# ===========================================================================


@pytest.mark.skip(reason="US10-TK02")
@pytest.mark.asyncio
async def test_connect_tracker_invalid_user_disconnects():
    """connect com X-User-Id inválido (usuário não existe) deve emitir error e desconectar."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    sid = "sid-test-001"
    environ = {
        "QUERY_STRING": f"trip_id={_make_trip_id()}&role=tracker&user_id={_make_user_id()}"
    }

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit, \
         patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc:
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


@pytest.mark.skip(reason="US10-TK02")
@pytest.mark.asyncio
async def test_connect_tracker_not_route_driver_disconnects():
    """connect com tracker que não é o motorista da trip deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "sid-test-002"

    with patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc, \
         patch("src.infrastructure.socketio.server._validate_tracker", return_value=False):
        environ = {
            "QUERY_STRING": f"trip_id={_make_trip_id()}&role=tracker&user_id={_make_user_id()}"
        }
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


# ===========================================================================
# US10-TK03 — join_session (tracker) + session_joined
# ===========================================================================


@pytest.mark.skip(reason="US10-TK03")
@pytest.mark.asyncio
async def test_join_session_tracker_creates_session():
    """join_session tracker deve criar entrada em tracking_sessions."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-sid-001"
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock), \
         patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["join_session"](sid, {"trip_id": trip_id, "role": "tracker"})

        assert trip_id in tracking_sessions
        assert tracking_sessions[trip_id]["tracker_sid"] == sid

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


@pytest.mark.skip(reason="US10-TK03")
@pytest.mark.asyncio
async def test_join_session_tracker_emits_session_joined():
    """join_session tracker deve emitir session_joined com follower_count."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-sid-002"
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock), \
         patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["join_session"](sid, {"trip_id": trip_id, "role": "tracker"})

        mock_emit.assert_called_once()
        call_event = mock_emit.call_args[0][0]
        assert call_event == "session_joined"

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


# ===========================================================================
# US10-TK04 — location_update + broadcast
# ===========================================================================


@pytest.mark.skip(reason="US10-TK04")
@pytest.mark.asyncio
async def test_location_update_saves_last_location():
    """location_update deve salvar last_location no estado da sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-loc-001"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": [], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.2, "heading": 90.0, "speed": 40.0, "timestamp": "2026-01-01T08:00:00Z"}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await sio.handlers["/"]["location_update"](sid, payload)

    assert tracking_sessions[trip_id]["last_location"] == payload

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


@pytest.mark.skip(reason="US10-TK04")
@pytest.mark.asyncio
async def test_location_update_broadcasts_to_room():
    """location_update deve fazer broadcast para o room da sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-loc-002"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": ["follower-sid-1"], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.2, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["location_update"](sid, payload)
        mock_emit.assert_called_once()
        call_room = mock_emit.call_args[1].get("room") or mock_emit.call_args[0][2]
        assert trip_id in call_room

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


@pytest.mark.skip(reason="US10-TK04")
@pytest.mark.asyncio
async def test_location_update_non_tracker_ignored():
    """location_update emitido por follower deve ser ignorado silenciosamente."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "follower-loc-001"
    tracking_sessions[trip_id] = {"tracker_sid": "outro-sid", "followers": [sid], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["location_update"](sid, {"lat": 0.0, "lng": 0.0})
        mock_emit.assert_not_called()

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


# ===========================================================================
# US10-TK05 — disconnect + tracker_disconnected + cleanup
# ===========================================================================


@pytest.mark.skip(reason="US10-TK05")
@pytest.mark.asyncio
async def test_disconnect_tracker_emits_tracker_disconnected():
    """disconnect do tracker deve emitir tracker_disconnected para followers."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-disc-001"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": ["follower-1"], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["disconnect"](sid)

        mock_emit.assert_called_once()
        assert mock_emit.call_args[0][0] == "tracker_disconnected"

    tracking_sessions.pop(trip_id, None)


@pytest.mark.skip(reason="US10-TK05")
@pytest.mark.asyncio
async def test_disconnect_tracker_clears_tracker_sid():
    """disconnect do tracker deve setar tracker_sid para None na sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-disc-002"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": ["f1"], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await sio.handlers["/"]["disconnect"](sid)

    assert tracking_sessions[trip_id]["tracker_sid"] is None
    tracking_sessions.pop(trip_id, None)


@pytest.mark.skip(reason="US10-TK05")
@pytest.mark.asyncio
async def test_disconnect_removes_empty_session():
    """disconnect com sessão sem tracker e sem followers deve remover da memória."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-disc-003"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": [], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await sio.handlers["/"]["disconnect"](sid)

    assert trip_id not in tracking_sessions


# ===========================================================================
# US11-TK02 — autenticação do follower (vínculo ativo)
# ===========================================================================


@pytest.mark.skip(reason="US11-TK02")
@pytest.mark.asyncio
async def test_connect_follower_without_active_membership_disconnects():
    """connect com role follower sem vínculo ativo deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "follower-auth-001"
    environ = {
        "QUERY_STRING": f"trip_id={_make_trip_id()}&role=follower&user_id={_make_user_id()}"
    }

    with patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc, \
         patch("src.infrastructure.socketio.server._validate_follower", return_value=False):
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


@pytest.mark.skip(reason="US11-TK02")
@pytest.mark.asyncio
async def test_connect_follower_with_active_membership_allowed():
    """connect com role follower com vínculo ativo (accepted/pending) não deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "follower-auth-002"
    environ = {
        "QUERY_STRING": f"trip_id={_make_trip_id()}&role=follower&user_id={_make_user_id()}"
    }

    with patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc, \
         patch("src.infrastructure.socketio.server._validate_follower", return_value=True), \
         patch("src.infrastructure.socketio.server._validate_tracker", return_value=True):
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_not_called()


# ===========================================================================
# US11-TK03 — join_session (follower) + session_joined com last_location
# ===========================================================================


@pytest.mark.skip(reason="US11-TK03")
@pytest.mark.asyncio
async def test_join_session_follower_registered_in_followers():
    """join_session follower deve adicionar o sid à lista de followers da sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-exist-001"
    follower_sid = "follower-join-001"

    tracking_sessions[trip_id] = {"tracker_sid": tracker_sid, "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock), \
         patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

    assert follower_sid in tracking_sessions[trip_id]["followers"]

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.skip(reason="US11-TK03")
@pytest.mark.asyncio
async def test_join_session_follower_receives_last_location():
    """join_session follower deve incluir last_location no session_joined se disponível."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    last_loc = {"lat": -30.1, "lng": -51.3, "heading": 45.0, "speed": 30.0, "timestamp": "2026-01-01T08:05:00Z"}
    follower_sid = "follower-join-002"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-x", "followers": [], "last_location": last_loc}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock), \
         patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

        call_data = mock_emit.call_args[0][1]
        assert "last_location" in call_data
        assert call_data["last_location"] == last_loc

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.skip(reason="US11-TK03")
@pytest.mark.asyncio
async def test_join_session_follower_tracker_online_true_when_connected():
    """session_joined para follower deve indicar tracker_online=True quando tracker está conectado."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    follower_sid = "follower-join-003"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-online", "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock), \
         patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

        call_data = mock_emit.call_args[0][1]
        assert call_data.get("tracker_online") is True

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


# ===========================================================================
# US11-TK04 — trip_finished event + TripService integration
# ===========================================================================


@pytest.mark.skip(reason="US11-TK04")
@pytest.mark.asyncio
async def test_trip_finished_emits_to_room():
    """emit_trip_finished deve emitir trip_finished para todos no room da sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1", "f2"], "last_location": None}

    from src.infrastructure.socketio.server import emit_trip_finished

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await emit_trip_finished(trip_id)
        mock_emit.assert_called_once()
        assert mock_emit.call_args[0][0] == "trip_finished"

    tracking_sessions.pop(trip_id, None)


@pytest.mark.skip(reason="US11-TK04")
@pytest.mark.asyncio
async def test_trip_finished_clears_session_state():
    """emit_trip_finished deve remover a sessão do estado em memória."""
    from src.infrastructure.socketio.server import emit_trip_finished, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_trip_finished(trip_id)

    assert trip_id not in tracking_sessions


@pytest.mark.skip(reason="US11-TK04")
@pytest.mark.asyncio
async def test_trip_finished_no_error_when_session_not_found():
    """emit_trip_finished com trip_id sem sessão ativa não deve levantar exceção."""
    from src.infrastructure.socketio.server import emit_trip_finished

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_trip_finished(str(uuid.uuid4()))  # sem sessão — não deve explodir
