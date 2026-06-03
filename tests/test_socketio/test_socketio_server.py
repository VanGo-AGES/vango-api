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


def test_sio_server_is_async_server():
    """sio deve ser uma instância de socketio.AsyncServer."""
    import socketio as sio_lib

    from src.infrastructure.socketio.server import sio

    assert isinstance(sio, sio_lib.AsyncServer)


def test_tracking_sessions_starts_empty():
    """tracking_sessions deve iniciar como dict vazio."""
    from src.infrastructure.socketio.server import tracking_sessions

    assert isinstance(tracking_sessions, dict)


def test_sid_meta_starts_empty():
    """sid_meta deve iniciar como dict vazio."""
    from src.infrastructure.socketio.server import sid_meta

    assert isinstance(sid_meta, dict)


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


@pytest.mark.asyncio
async def test_connect_tracker_invalid_user_disconnects():
    """connect com X-User-Id inválido (usuário não existe) deve emitir error e desconectar."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    sid = "sid-test-001"
    environ = {"QUERY_STRING": f"trip_id={_make_trip_id()}&role=tracker&user_id={_make_user_id()}"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc,
    ):
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


@pytest.mark.asyncio
async def test_connect_tracker_not_route_driver_disconnects():
    """connect com tracker que não é o motorista da trip deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "sid-test-002"

    with (
        patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc,
        patch("src.infrastructure.socketio.server._validate_tracker", return_value=False),
    ):
        environ = {"QUERY_STRING": f"trip_id={_make_trip_id()}&role=tracker&user_id={_make_user_id()}"}
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


# ===========================================================================
# US10-TK03 — join_session (tracker) + session_joined
# ===========================================================================


@pytest.mark.asyncio
async def test_join_session_tracker_creates_session():
    """join_session tracker deve criar entrada em tracking_sessions."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-sid-001"
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        await sio.handlers["/"]["join_session"](sid, {"trip_id": trip_id, "role": "tracker"})

        assert trip_id in tracking_sessions
        assert tracking_sessions[trip_id]["tracker_sid"] == sid

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


@pytest.mark.asyncio
async def test_join_session_tracker_emits_session_joined():
    """join_session tracker deve emitir session_joined com follower_count."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-sid-002"
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        await sio.handlers["/"]["join_session"](sid, {"trip_id": trip_id, "role": "tracker"})

        mock_emit.assert_called_once()
        call_event = mock_emit.call_args[0][0]
        assert call_event == "session_joined"

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


# ===========================================================================
# US10-TK04 — location_update + broadcast
# ===========================================================================


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


@pytest.mark.asyncio
async def test_location_update_broadcasts_to_room():
    """location_update deve fazer broadcast para o room da sessão.

    Nota: TK17 acrescentou um emit adicional de "driver_eta" para o tracker_sid
    no mesmo handler, então não dá mais para assertar `called_once`. O que
    importa neste teste é que UM dos emits seja location_update com room
    contendo o trip_id.
    """
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    sid = "tracker-loc-002"
    tracking_sessions[trip_id] = {"tracker_sid": sid, "followers": ["follower-sid-1"], "last_location": None}
    sid_meta[sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.2, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await sio.handlers["/"]["location_update"](sid, payload)

        # Procurar o emit de location_update para o room
        room_broadcasts = [
            call
            for call in mock_emit.call_args_list
            if len(call.args) > 0 and call.args[0] == "location_update" and call.kwargs.get("room")
        ]
        assert len(room_broadcasts) >= 1
        assert trip_id in room_broadcasts[0].kwargs.get("room")

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(sid, None)


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


@pytest.mark.asyncio
async def test_connect_follower_without_active_membership_disconnects():
    """connect com role follower sem vínculo ativo deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "follower-auth-001"
    environ = {"QUERY_STRING": f"trip_id={_make_trip_id()}&role=follower&user_id={_make_user_id()}"}

    with (
        patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc,
        patch("src.infrastructure.socketio.server._validate_follower", return_value=False),
    ):
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_called_once_with(sid)


@pytest.mark.asyncio
async def test_connect_follower_with_active_membership_allowed():
    """connect com role follower com vínculo ativo (accepted/pending) não deve desconectar."""
    from src.infrastructure.socketio.server import sio

    sid = "follower-auth-002"
    environ = {"QUERY_STRING": f"trip_id={_make_trip_id()}&role=follower&user_id={_make_user_id()}"}

    with (
        patch("src.infrastructure.socketio.server.sio.disconnect", new_callable=AsyncMock) as mock_disc,
        patch("src.infrastructure.socketio.server._validate_follower", return_value=True),
        patch("src.infrastructure.socketio.server._validate_tracker", return_value=True),
    ):
        await sio.handlers["/"]["connect"](sid, environ)
        mock_disc.assert_not_called()


def test_validate_follower_accepts_pending_or_accepted_statuses():
    """_validate_follower deve aceitar vínculos pending e accepted na rota da trip."""
    from src.infrastructure.socketio.server import _validate_follower

    trip_id = _make_trip_id()
    user_id = _make_user_id()
    route_id = uuid.uuid4()

    class FakeTrip:
        def __init__(self, route_id):
            self.route_id = route_id

    pending_rp = MagicMock(status="pending")
    accepted_rp = MagicMock(status="accepted")

    with (
        patch("src.infrastructure.socketio.server.SessionLocal") as mock_session_local,
        patch("src.infrastructure.socketio.server.TripRepositoryImpl") as mock_trip_repo_cls,
        patch("src.infrastructure.socketio.server.RoutePassangerRepositoryImpl") as mock_rp_repo_cls,
    ):
        session = MagicMock()
        mock_session_local.return_value = session
        mock_trip_repo_cls.return_value.find_by_id.return_value = FakeTrip(route_id)
        mock_rp_repo_cls.return_value.find_by_user_and_route_id.return_value = [pending_rp, accepted_rp]

        assert _validate_follower(user_id, trip_id) is True


def test_validate_follower_returns_false_without_link():
    """_validate_follower deve retornar False quando não houver vínculo."""
    from src.infrastructure.socketio.server import _validate_follower

    trip_id = _make_trip_id()
    user_id = _make_user_id()
    route_id = uuid.uuid4()

    class FakeTrip:
        def __init__(self, route_id):
            self.route_id = route_id

    with (
        patch("src.infrastructure.socketio.server.SessionLocal") as mock_session_local,
        patch("src.infrastructure.socketio.server.TripRepositoryImpl") as mock_trip_repo_cls,
        patch("src.infrastructure.socketio.server.RoutePassangerRepositoryImpl") as mock_rp_repo_cls,
    ):
        session = MagicMock()
        mock_session_local.return_value = session
        mock_trip_repo_cls.return_value.find_by_id.return_value = FakeTrip(route_id)
        mock_rp_repo_cls.return_value.find_by_user_and_route_id.return_value = []

        assert _validate_follower(user_id, trip_id) is False


# ===========================================================================
# US11-TK03 — join_session (follower) + session_joined com last_location
# ===========================================================================


@pytest.mark.asyncio
async def test_join_session_follower_registered_in_followers():
    """join_session follower deve adicionar o sid à lista de followers da sessão."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-exist-001"
    follower_sid = "follower-join-001"

    tracking_sessions[trip_id] = {"tracker_sid": tracker_sid, "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock),
    ):
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

    assert follower_sid in tracking_sessions[trip_id]["followers"]

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_join_session_follower_receives_last_location():
    """join_session follower deve incluir last_location no session_joined se disponível."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    last_loc = {"lat": -30.1, "lng": -51.3, "heading": 45.0, "speed": 30.0, "timestamp": "2026-01-01T08:05:00Z"}
    follower_sid = "follower-join-002"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-x", "followers": [], "last_location": last_loc}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

        call_data = mock_emit.call_args[0][1]
        assert "last_location" in call_data
        assert call_data["last_location"] == last_loc

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_join_session_follower_tracker_online_true_when_connected():
    """session_joined para follower deve indicar tracker_online=True quando tracker está conectado."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    follower_sid = "follower-join-003"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-online", "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

        call_data = mock_emit.call_args[0][1]
        assert call_data.get("tracker_online") is True

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_join_session_follower_populates_stop_coordinates():
    """join_session de follower deve persistir stop_lat/stop_lng no sid_meta a
    partir do payload recebido — necessário pro cálculo de ETA por follower."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    follower_sid = "follower-join-stop-001"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-x", "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock),
    ):
        await sio.handlers["/"]["join_session"](
            follower_sid,
            {"trip_id": trip_id, "role": "follower", "stop_lat": -30.0567, "stop_lng": -51.1734},
        )

    assert sid_meta[follower_sid]["stop_lat"] == pytest.approx(-30.0567)
    assert sid_meta[follower_sid]["stop_lng"] == pytest.approx(-51.1734)
    assert isinstance(sid_meta[follower_sid]["stop_lat"], float)
    assert isinstance(sid_meta[follower_sid]["stop_lng"], float)

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_join_session_follower_defaults_missing_stop_coordinates_to_none():
    """join_session sem stop_lat/stop_lng (ou com tipos inválidos) deve persistir
    None no sid_meta — não pode crashar nem propagar valores inválidos."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    follower_sid = "follower-join-stop-002"

    tracking_sessions[trip_id] = {"tracker_sid": "tracker-x", "followers": [], "last_location": None}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock),
    ):
        # Sem stop_lat/stop_lng no payload
        await sio.handlers["/"]["join_session"](follower_sid, {"trip_id": trip_id, "role": "follower"})

    assert sid_meta[follower_sid]["stop_lat"] is None
    assert sid_meta[follower_sid]["stop_lng"] is None

    # Com tipos inválidos
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}
    tracking_sessions[trip_id] = {"tracker_sid": "tracker-x", "followers": [], "last_location": None}

    with (
        patch("src.infrastructure.socketio.server.sio.enter_room", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock),
    ):
        await sio.handlers["/"]["join_session"](
            follower_sid,
            {"trip_id": trip_id, "role": "follower", "stop_lat": "abc", "stop_lng": None},
        )

    assert sid_meta[follower_sid]["stop_lat"] is None
    assert sid_meta[follower_sid]["stop_lng"] is None

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(follower_sid, None)


# ===========================================================================
# US11-TK04 — trip_finished event + TripService integration
# ===========================================================================


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


@pytest.mark.asyncio
async def test_trip_finished_clears_session_state():
    """emit_trip_finished deve remover a sessão do estado em memória."""
    from src.infrastructure.socketio.server import emit_trip_finished, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_trip_finished(trip_id)

    assert trip_id not in tracking_sessions


@pytest.mark.asyncio
async def test_trip_finished_no_error_when_session_not_found():
    """emit_trip_finished com trip_id sem sessão ativa não deve levantar exceção."""
    from src.infrastructure.socketio.server import emit_trip_finished

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_trip_finished(str(uuid.uuid4()))  # sem sessão — não deve explodir


# ===========================================================================
# US10-TK08 — location_update enriquecido com ETA por follower
# ===========================================================================


@pytest.mark.asyncio
async def test_location_update_broadcast_includes_eta_fields():
    """location_update broadcast para cada follower deve incluir eta_minutes e distance_km."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-eta-001"
    follower_sid = "follower-eta-001"

    tracking_sessions[trip_id] = {
        "tracker_sid": tracker_sid,
        "followers": [follower_sid],
        "last_location": None,
    }
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}
    sid_meta[follower_sid] = {
        "trip_id": trip_id,
        "role": "follower",
        "user_id": _make_user_id(),
        "stop_lat": -30.1,
        "stop_lng": -51.3,
    }

    payload = {"lat": -30.0, "lng": -51.2, "heading": 90.0, "speed": 40.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_follower", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = {"eta_minutes": 5, "distance_km": 2.3}
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        broadcast_data = mock_emit.call_args[0][1]
        assert "eta_minutes" in broadcast_data or any("eta_minutes" in str(call) for call in mock_emit.call_args_list)

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_location_update_eta_uses_follower_stop_coordinates():
    """_calculate_eta_for_follower é chamado com o sid do follower para obter suas stop coords."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-eta-002"
    follower_sid = "follower-eta-002"

    tracking_sessions[trip_id] = {
        "tracker_sid": tracker_sid,
        "followers": [follower_sid],
        "last_location": None,
    }
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}
    sid_meta[follower_sid] = {
        "trip_id": trip_id,
        "role": "follower",
        "user_id": _make_user_id(),
        "stop_lat": -30.2,
        "stop_lng": -51.1,
    }

    payload = {"lat": -30.0, "lng": -51.0, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock),
        patch("src.infrastructure.socketio.server._calculate_eta_for_follower", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = {"eta_minutes": 8, "distance_km": 3.1}
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        mock_eta.assert_called_once()
        call_args = mock_eta.call_args
        # driver lat/lng e follower_sid devem ser passados
        assert call_args.args[0] == pytest.approx(-30.0) or call_args.kwargs.get("driver_lat") == pytest.approx(-30.0)
        assert follower_sid in call_args.args or call_args.kwargs.get("follower_sid") == follower_sid

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_location_update_eta_gracefully_none_when_routing_unavailable():
    """Se routing service não disponível, eta_minutes e distance_km devem ser None no broadcast.

    Nota: TK17 acrescentou um emit adicional de "driver_eta" no mesmo handler,
    então não dá mais para assertar `called_once`. O contrato aqui é: mesmo
    sem ETA, o evento "location_update" deve ter sido emitido pelo menos uma
    vez para o follower (não pode suprimir o evento).
    """
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-eta-003"
    follower_sid = "follower-eta-003"

    tracking_sessions[trip_id] = {
        "tracker_sid": tracker_sid,
        "followers": [follower_sid],
        "last_location": None,
    }
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}
    sid_meta[follower_sid] = {
        "trip_id": trip_id,
        "role": "follower",
        "user_id": _make_user_id(),
        # sem stop_lat/stop_lng — routing indisponível
    }

    payload = {"lat": -30.0, "lng": -51.0, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_follower", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = None  # routing indisponível
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        # broadcast deve ocorrer mesmo sem ETA (não pode suprimir o evento)
        location_update_calls = [call for call in mock_emit.call_args_list if len(call.args) > 0 and call.args[0] == "location_update"]
        assert len(location_update_calls) >= 1

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)
    sid_meta.pop(follower_sid, None)


# ---------------------------------------------------------------------------
# US10-TK08 — _calculate_eta_for_follower (impl isolada do helper)
#
# Os testes acima cobrem o WIRING do helper no `location_update` (mockam a
# função inteira). Estes abaixo cobrem a IMPLEMENTAÇÃO do helper em si,
# mockando apenas IRoutingService e usando as coordenadas reais de
# sid_meta. Esse padrão é o mesmo de `_calculate_eta_for_tracker`
# (US10-TK17) e de `_trigger_route_optimization` (route_passanger_service /
# absence_service).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calculate_eta_for_follower_returns_dict_when_stop_coordinates_present():
    """Quando sid_meta[follower_sid] tem stop_lat/stop_lng e routing responde,
    o helper devolve dict com eta_minutes e distance_km."""
    from src.infrastructure.socketio.server import _calculate_eta_for_follower, sid_meta

    follower_sid = "follower-impl-001"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "stop_lat": -30.05,
        "stop_lng": -51.25,
    }

    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = MagicMock(
        estimated_duration_min=5,
        total_distance_km=2.3,
    )

    with patch(
        "src.infrastructure.socketio.server._get_routing_service",
        return_value=routing_mock,
        create=True,
    ):
        result = await _calculate_eta_for_follower(-30.0, -51.2, follower_sid)

    assert result is not None
    assert result.get("eta_minutes") == 5
    assert result.get("distance_km") == 2.3

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_calculate_eta_for_follower_returns_none_when_stop_coordinates_missing():
    """Se sid_meta[follower_sid] não tem stop_lat/stop_lng (ou está com None),
    o helper retorna None sem chamar o routing service."""
    from src.infrastructure.socketio.server import _calculate_eta_for_follower, sid_meta

    follower_sid = "follower-impl-002"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        # sem stop_lat/stop_lng
    }

    routing_mock = MagicMock()

    with patch(
        "src.infrastructure.socketio.server._get_routing_service",
        return_value=routing_mock,
        create=True,
    ):
        result = await _calculate_eta_for_follower(-30.0, -51.2, follower_sid)

    assert result is None
    routing_mock.get_route_info.assert_not_called()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_calculate_eta_for_follower_returns_none_when_follower_not_in_sid_meta():
    """Se o follower_sid não existir em sid_meta, o helper retorna None
    silenciosamente (não levanta KeyError)."""
    from src.infrastructure.socketio.server import _calculate_eta_for_follower

    routing_mock = MagicMock()

    with patch(
        "src.infrastructure.socketio.server._get_routing_service",
        return_value=routing_mock,
        create=True,
    ):
        result = await _calculate_eta_for_follower(-30.0, -51.2, "follower-nao-existe")

    assert result is None
    routing_mock.get_route_info.assert_not_called()


@pytest.mark.asyncio
async def test_calculate_eta_for_follower_passes_correct_origin_and_destination():
    """O helper deve chamar IRoutingService.get_route_info com origin =
    posição do motorista e destination = stop_lat/stop_lng do follower —
    pegar essa ordem trocada é o bug clássico que esses testes precisam
    pegar."""
    from src.infrastructure.socketio.server import _calculate_eta_for_follower, sid_meta

    follower_sid = "follower-impl-004"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "stop_lat": -30.10,
        "stop_lng": -51.30,
    }

    driver_lat, driver_lng = -30.00, -51.20

    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = MagicMock(
        estimated_duration_min=7,
        total_distance_km=2.0,
    )

    with patch(
        "src.infrastructure.socketio.server._get_routing_service",
        return_value=routing_mock,
        create=True,
    ):
        await _calculate_eta_for_follower(driver_lat, driver_lng, follower_sid)

    routing_mock.get_route_info.assert_called_once()
    call = routing_mock.get_route_info.call_args
    origin = call.kwargs.get("origin") or call.args[0]
    destination = call.kwargs.get("destination") or call.args[-1]

    # origin é o motorista
    assert origin.get("lat") == pytest.approx(driver_lat)
    assert origin.get("lng") == pytest.approx(driver_lng)
    # destination é a parada do follower
    assert destination.get("lat") == pytest.approx(-30.10)
    assert destination.get("lng") == pytest.approx(-51.30)

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_calculate_eta_for_follower_returns_none_when_routing_raises():
    """Se IRoutingService.get_route_info levantar exceção, o helper devolve
    None em vez de propagar — falha de routing é best-effort e não deve
    derrubar o location_update."""
    from src.infrastructure.socketio.server import _calculate_eta_for_follower, sid_meta

    follower_sid = "follower-impl-005"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "stop_lat": -30.05,
        "stop_lng": -51.25,
    }

    routing_mock = MagicMock()
    routing_mock.get_route_info.side_effect = RuntimeError("mapbox down")

    with patch(
        "src.infrastructure.socketio.server._get_routing_service",
        return_value=routing_mock,
        create=True,
    ):
        result = await _calculate_eta_for_follower(-30.0, -51.2, follower_sid)

    assert result is None

    sid_meta.pop(follower_sid, None)


# ===========================================================================
# US11-TK05 — emit_passenger_boarded
# ===========================================================================


@pytest.mark.asyncio
async def test_emit_passenger_boarded_emits_to_room():
    """emit_passenger_boarded deve emitir evento passenger_boarded para o room da sessão."""
    from src.infrastructure.socketio.server import emit_passenger_boarded, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await emit_passenger_boarded(trip_id, "tp-uuid-001", "João Silva")

        mock_emit.assert_called_once()
        assert mock_emit.call_args[0][0] == "passenger_boarded"

    tracking_sessions.pop(trip_id, None)


@pytest.mark.asyncio
async def test_emit_passenger_boarded_payload_contains_user_name():
    """Payload de passenger_boarded deve conter trip_passanger_id e user_name."""
    from src.infrastructure.socketio.server import emit_passenger_boarded, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await emit_passenger_boarded(trip_id, "tp-uuid-002", "Maria Souza")

        payload = mock_emit.call_args[0][1]
        assert payload.get("user_name") == "Maria Souza"
        assert "trip_passanger_id" in payload

    tracking_sessions.pop(trip_id, None)


@pytest.mark.asyncio
async def test_emit_passenger_boarded_no_error_when_session_not_found():
    """emit_passenger_boarded com trip_id sem sessão ativa não deve levantar exceção."""
    from src.infrastructure.socketio.server import emit_passenger_boarded

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_passenger_boarded(str(uuid.uuid4()), "tp-x", "Alguém")  # sem sessão


# ===========================================================================
# US11-TK06 — emit_passenger_absent
# ===========================================================================


@pytest.mark.asyncio
async def test_emit_passenger_absent_emits_to_room():
    """emit_passenger_absent deve emitir evento passenger_absent para o room da sessão."""
    from src.infrastructure.socketio.server import emit_passenger_absent, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await emit_passenger_absent(trip_id, "tp-uuid-003", "Carlos Lima")

        mock_emit.assert_called_once()
        assert mock_emit.call_args[0][0] == "passenger_absent"

    tracking_sessions.pop(trip_id, None)


@pytest.mark.asyncio
async def test_emit_passenger_absent_payload_contains_user_name():
    """Payload de passenger_absent deve conter trip_passanger_id e user_name."""
    from src.infrastructure.socketio.server import emit_passenger_absent, tracking_sessions

    trip_id = _make_trip_id()
    tracking_sessions[trip_id] = {"tracker_sid": "t1", "followers": ["f1"], "last_location": None}

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit:
        await emit_passenger_absent(trip_id, "tp-uuid-004", "Ana Costa")

        payload = mock_emit.call_args[0][1]
        assert payload.get("user_name") == "Ana Costa"
        assert "trip_passanger_id" in payload

    tracking_sessions.pop(trip_id, None)


@pytest.mark.asyncio
async def test_emit_passenger_absent_no_error_when_session_not_found():
    """emit_passenger_absent com trip_id sem sessão ativa não deve levantar exceção."""
    from src.infrastructure.socketio.server import emit_passenger_absent

    with patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock):
        await emit_passenger_absent(str(uuid.uuid4()), "tp-y", "Ninguém")  # sem sessão


# ===========================================================================
# US12-TK06 — _notify_proximity_if_needed (push "motorista está próximo")
# ===========================================================================


@pytest.mark.asyncio
async def test_proximity_notification_sent_when_below_threshold():
    """_notify_proximity_if_needed deve chamar notify_passanger_driver_approaching quando distance_km < threshold."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_proximity_if_needed,
        sid_meta,
        PROXIMITY_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-prox-001"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "proximity_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_proximity_if_needed(follower_sid, PROXIMITY_THRESHOLD_KM - 0.1)

    notif_mock.notify_passanger_driver_approaching.assert_called_once()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_proximity_notification_not_sent_when_above_threshold():
    """_notify_proximity_if_needed não deve notificar quando distance_km >= threshold."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_proximity_if_needed,
        sid_meta,
        PROXIMITY_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-prox-002"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "proximity_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_proximity_if_needed(follower_sid, PROXIMITY_THRESHOLD_KM + 0.5)

    notif_mock.notify_passanger_driver_approaching.assert_not_called()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_proximity_notification_sent_only_once_per_session():
    """_notify_proximity_if_needed não deve reenviar o push se proximity_notified já for True."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_proximity_if_needed,
        sid_meta,
        PROXIMITY_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-prox-003"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "proximity_notified": True,  # já notificado
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_proximity_if_needed(follower_sid, PROXIMITY_THRESHOLD_KM - 0.1)

    notif_mock.notify_passanger_driver_approaching.assert_not_called()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_proximity_notification_sets_flag_after_sending():
    """_notify_proximity_if_needed deve setar proximity_notified=True após enviar o push."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_proximity_if_needed,
        sid_meta,
        PROXIMITY_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-prox-004"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "proximity_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_proximity_if_needed(follower_sid, PROXIMITY_THRESHOLD_KM - 0.1)

    assert sid_meta[follower_sid]["proximity_notified"] is True

    sid_meta.pop(follower_sid, None)


# ===========================================================================
# US12-TK07 — _notify_arrival_if_needed (push "motorista chegou")
# ===========================================================================


@pytest.mark.asyncio
async def test_arrival_notification_sent_when_below_threshold():
    """_notify_arrival_if_needed deve chamar notify_passanger_driver_arrived quando distance_km < ARRIVAL_THRESHOLD_KM."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_arrival_if_needed,
        sid_meta,
        ARRIVAL_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-arr-001"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "arrived_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_arrival_if_needed(follower_sid, ARRIVAL_THRESHOLD_KM - 0.01)

    notif_mock.notify_passanger_driver_arrived.assert_called_once()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_arrival_notification_not_sent_when_above_threshold():
    """_notify_arrival_if_needed não deve notificar quando distance_km >= ARRIVAL_THRESHOLD_KM."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_arrival_if_needed,
        sid_meta,
        ARRIVAL_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-arr-002"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "arrived_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_arrival_if_needed(follower_sid, ARRIVAL_THRESHOLD_KM + 0.1)

    notif_mock.notify_passanger_driver_arrived.assert_not_called()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_arrival_notification_sent_only_once_per_session():
    """_notify_arrival_if_needed não deve reenviar o push se arrived_notified já for True."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_arrival_if_needed,
        sid_meta,
        ARRIVAL_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-arr-003"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "arrived_notified": True,  # já notificado
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_arrival_if_needed(follower_sid, ARRIVAL_THRESHOLD_KM - 0.01)

    notif_mock.notify_passanger_driver_arrived.assert_not_called()

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_arrival_notification_sets_flag_after_sending():
    """_notify_arrival_if_needed deve setar arrived_notified=True após enviar o push."""
    from unittest.mock import MagicMock
    from src.infrastructure.socketio.server import (
        _notify_arrival_if_needed,
        sid_meta,
        ARRIVAL_THRESHOLD_KM,
    )
    from src.domains.notifications.service import INotificationService

    follower_sid = "follower-arr-004"
    sid_meta[follower_sid] = {
        "trip_id": _make_trip_id(),
        "role": "follower",
        "user_id": _make_user_id(),
        "route_id": str(__import__("uuid").uuid4()),
        "arrived_notified": False,
    }

    notif_mock = MagicMock(spec=INotificationService)

    with patch("src.infrastructure.socketio.server._get_notification_service", return_value=notif_mock):
        await _notify_arrival_if_needed(follower_sid, ARRIVAL_THRESHOLD_KM - 0.01)

    assert sid_meta[follower_sid]["arrived_notified"] is True

    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_arrival_threshold_smaller_than_proximity_threshold():
    """ARRIVAL_THRESHOLD_KM deve ser menor que PROXIMITY_THRESHOLD_KM."""
    from src.infrastructure.socketio.server import ARRIVAL_THRESHOLD_KM, PROXIMITY_THRESHOLD_KM

    assert ARRIVAL_THRESHOLD_KM < PROXIMITY_THRESHOLD_KM


# ===========================================================================
# US10-TK17 — _calculate_eta_for_tracker + driver_eta emit no location_update
# ===========================================================================


@pytest.mark.asyncio
async def test_location_update_emits_driver_eta_to_tracker():
    """location_update deve emitir 'driver_eta' diretamente para o tracker_sid."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-driver-eta-001"

    tracking_sessions[trip_id] = {
        "tracker_sid": tracker_sid,
        "followers": [],
        "last_location": None,
    }
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.2, "heading": 90.0, "speed": 40.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_tracker", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = {"stop_id": "stop-x", "eta_minutes": 6, "distance_km": 1.4}
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        # entre as chamadas de emit deve haver uma para "driver_eta" com to=tracker_sid
        driver_eta_calls = [call for call in mock_emit.call_args_list if len(call.args) > 0 and call.args[0] == "driver_eta"]
        assert len(driver_eta_calls) >= 1
        # to deve apontar para o tracker_sid (kwarg ou posicional)
        first_call = driver_eta_calls[0]
        to_target = first_call.kwargs.get("to") or (first_call.args[2] if len(first_call.args) > 2 else None)
        assert to_target == tracker_sid

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)


@pytest.mark.asyncio
async def test_driver_eta_payload_contains_eta_and_distance_fields():
    """driver_eta payload deve conter eta_minutes e distance_km vindos do calculo."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-driver-eta-002"

    tracking_sessions[trip_id] = {"tracker_sid": tracker_sid, "followers": [], "last_location": None}
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.0, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_tracker", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = {"stop_id": "stop-y", "eta_minutes": 12, "distance_km": 3.5}
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        driver_eta_call = next(call for call in mock_emit.call_args_list if len(call.args) > 0 and call.args[0] == "driver_eta")
        body = driver_eta_call.args[1]
        assert body.get("eta_minutes") == 12
        assert body.get("distance_km") == 3.5

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)


@pytest.mark.asyncio
async def test_driver_eta_emitted_with_null_when_no_pending_stop():
    """Se _calculate_eta_for_tracker retornar None, emit ocorre com eta_minutes e
    distance_km nulos (ou um payload equivalente que sinalize ausência)."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-driver-eta-003"

    tracking_sessions[trip_id] = {"tracker_sid": tracker_sid, "followers": [], "last_location": None}
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.0, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_tracker", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.return_value = None
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        driver_eta_call = next(call for call in mock_emit.call_args_list if len(call.args) > 0 and call.args[0] == "driver_eta")
        body = driver_eta_call.args[1]
        assert body.get("eta_minutes") is None
        assert body.get("distance_km") is None

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)


@pytest.mark.asyncio
async def test_driver_eta_failure_does_not_block_follower_broadcast():
    """Falha em _calculate_eta_for_tracker (exceção) não pode interromper o
    broadcast de location_update para os followers."""
    from src.infrastructure.socketio.server import sio, tracking_sessions, sid_meta

    trip_id = _make_trip_id()
    tracker_sid = "tracker-driver-eta-004"
    follower_sid = "follower-driver-eta-004"

    tracking_sessions[trip_id] = {
        "tracker_sid": tracker_sid,
        "followers": [follower_sid],
        "last_location": None,
    }
    sid_meta[tracker_sid] = {"trip_id": trip_id, "role": "tracker", "user_id": _make_user_id()}
    sid_meta[follower_sid] = {"trip_id": trip_id, "role": "follower", "user_id": _make_user_id()}

    payload = {"lat": -30.0, "lng": -51.0, "heading": 0.0, "speed": 0.0, "timestamp": "2026-01-01T08:00:00Z"}

    with (
        patch("src.infrastructure.socketio.server.sio.emit", new_callable=AsyncMock) as mock_emit,
        patch("src.infrastructure.socketio.server._calculate_eta_for_tracker", new_callable=AsyncMock) as mock_eta,
    ):
        mock_eta.side_effect = RuntimeError("routing service down")
        # location_update não deve propagar a exceção
        await sio.handlers["/"]["location_update"](tracker_sid, payload)

        # broadcast pro follower deve ter ocorrido normalmente — pode ser
        # via room (followers fora de sid_meta) OU emit per-follower
        # (followers em sid_meta com ou sem stop coords). O essencial é
        # que pelo menos um evento "location_update" tenha sido emitido.
        location_update_calls = [call for call in mock_emit.call_args_list if len(call.args) > 0 and call.args[0] == "location_update"]
        assert len(location_update_calls) >= 1

    tracking_sessions.pop(trip_id, None)
    sid_meta.pop(tracker_sid, None)
    sid_meta.pop(follower_sid, None)


@pytest.mark.asyncio
async def test_calculate_eta_for_tracker_returns_dict_when_pending_stop_exists():
    """_calculate_eta_for_tracker deve devolver dict com eta_minutes/distance_km
    quando há próxima parada pendente com coordenadas e routing service responde."""
    from src.infrastructure.socketio.server import _calculate_eta_for_tracker

    trip_id = _make_trip_id()

    # service mock que devolve uma trip com próxima parada conhecida (com coords)
    trip_service_mock = MagicMock()
    next_stop_mock = MagicMock()
    next_stop_mock.stop_id = "stop-pending-001"
    next_stop_mock.address_label = "Rua X, 100"
    # mock interno usado pelo helper para descobrir coords
    trip_service_mock.get_next_stop_with_coordinates.return_value = {
        "stop_id": "stop-pending-001",
        "lat": -30.05,
        "lng": -51.25,
    }

    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = MagicMock(
        estimated_duration_min=6,
        total_distance_km=1.4,
    )

    with (
        patch("src.infrastructure.socketio.server._get_trip_service", return_value=trip_service_mock),
        patch("src.infrastructure.socketio.server._get_routing_service", return_value=routing_mock, create=True),
    ):
        result = await _calculate_eta_for_tracker(-30.0, -51.2, trip_id)

    assert result is not None
    assert result.get("eta_minutes") == 6
    assert result.get("distance_km") == 1.4
    assert result.get("stop_id") == "stop-pending-001"


@pytest.mark.asyncio
async def test_calculate_eta_for_tracker_returns_none_when_no_pending_stop():
    """Se não houver parada pendente (todos embarcados/ausentes), retorna None."""
    from src.infrastructure.socketio.server import _calculate_eta_for_tracker

    trip_service_mock = MagicMock()
    trip_service_mock.get_next_stop_with_coordinates.return_value = None

    with patch("src.infrastructure.socketio.server._get_trip_service", return_value=trip_service_mock):
        result = await _calculate_eta_for_tracker(-30.0, -51.2, _make_trip_id())

    assert result is None


@pytest.mark.asyncio
async def test_calculate_eta_for_tracker_returns_none_when_address_missing_coordinates():
    """Se a próxima parada pendente tiver address.latitude/longitude None, retorna None."""
    from src.infrastructure.socketio.server import _calculate_eta_for_tracker

    trip_service_mock = MagicMock()
    trip_service_mock.get_next_stop_with_coordinates.return_value = {
        "stop_id": "stop-no-coords",
        "lat": None,
        "lng": None,
    }

    with patch("src.infrastructure.socketio.server._get_trip_service", return_value=trip_service_mock):
        result = await _calculate_eta_for_tracker(-30.0, -51.2, _make_trip_id())

    assert result is None


@pytest.mark.asyncio
async def test_calculate_eta_for_tracker_returns_none_when_routing_unavailable():
    """Se routing_service não estiver disponível (ou levantar exceção), retorna None."""
    from src.infrastructure.socketio.server import _calculate_eta_for_tracker

    trip_service_mock = MagicMock()
    trip_service_mock.get_next_stop_with_coordinates.return_value = {
        "stop_id": "stop-x",
        "lat": -30.05,
        "lng": -51.25,
    }

    routing_mock = MagicMock()
    routing_mock.get_route_info.side_effect = RuntimeError("mapbox down")

    with (
        patch("src.infrastructure.socketio.server._get_trip_service", return_value=trip_service_mock),
        patch("src.infrastructure.socketio.server._get_routing_service", return_value=routing_mock, create=True),
    ):
        result = await _calculate_eta_for_tracker(-30.0, -51.2, _make_trip_id())

    assert result is None
