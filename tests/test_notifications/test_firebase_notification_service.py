"""US12-TK03 / TK04 / TK13 — Testes de FirebaseNotificationService.

TK03: verifica que a classe existe, implementa INotificationService, e que
      get_firebase_notification_service retorna uma instância válida.
TK04: verifica que cada método FCM envia a mensagem correta via Admin SDK
      (já mergeado — testes não-skipados validam que messaging.send foi
      chamado).
TK13: verifica que cada método FCM envia ALÉM da notification um payload
      `data` estruturado com pelo menos `type` e `routeId` (e `passengerId`
      quando aplicável) — necessário pra o app cliente rotear corretamente
      ao tocar na notificação. Todos os testes desta seção estão skipados
      até a impl ser feita.
"""

import uuid
from unittest.mock import Mock, patch

import pytest


# ===========================================================================
# US12-TK03 — infraestrutura base (classe + DI)
# ===========================================================================


def test_firebase_notification_service_implements_interface():
    """FirebaseNotificationService deve implementar INotificationService."""
    from src.domains.notifications.service import INotificationService
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    assert isinstance(service, INotificationService)


def test_firebase_notification_service_is_not_abstract():
    """FirebaseNotificationService não deve ser abstrata (instanciável)."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    # Não deve levantar TypeError
    service = FirebaseNotificationService()
    assert service is not None


def test_get_firebase_notification_service_returns_instance():
    """get_firebase_notification_service deve retornar FirebaseNotificationService."""
    from src.domains.notifications.service import INotificationService
    from src.infrastructure.dependencies.notification_dependencies import (
        get_firebase_notification_service,
    )

    service = get_firebase_notification_service()
    assert isinstance(service, INotificationService)


# ===========================================================================
# US12-TK04 — métodos FCM de execução de viagem (impl mergeada; testes
# abaixo seguem rodando, validam apenas que messaging.send foi chamado)
# ===========================================================================


def _make_trip_stub(status: str = "iniciada"):
    from src.domains.trips.entity import TripModel

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.route_id = uuid.uuid4()
    trip.vehicle_id = uuid.uuid4()
    trip.status = status
    return trip


def _make_trip_passanger_stub(status: str = "pendente"):
    from src.domains.trips.entity import TripPassangerModel

    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = uuid.uuid4()
    tp.route_passanger_id = uuid.uuid4()
    tp.status = status
    # cadeia tp.route_passanger.route_id usada pra montar data.routeId (TK13)
    tp.route_passanger = Mock()
    tp.route_passanger.id = tp.route_passanger_id
    tp.route_passanger.route_id = uuid.uuid4()
    return tp


def _make_rp_stub(status: str = "accepted"):
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = uuid.uuid4()
    rp.user_id = uuid.uuid4()
    rp.dependent_id = None
    rp.status = status
    return rp


def _sent_message(mock_send):
    """Extrai o objeto messaging.Message passado pra messaging.send."""
    assert mock_send.call_count >= 1
    return mock_send.call_args.args[0]


def test_firebase_notify_trip_started_sends_fcm():
    """notify_trip_started deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    trip = _make_trip_stub(status="iniciada")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_started(trip)
        mock_send.assert_called_once()



def test_firebase_notify_trip_arriving_at_stop_sends_fcm():
    """notify_trip_arriving_at_stop deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="pendente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_arriving_at_stop(tp)
        mock_send.assert_called_once()



def test_firebase_notify_trip_finished_sends_fcm():
    """notify_trip_finished deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    trip = _make_trip_stub(status="finalizada")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_finished(trip)
        mock_send.assert_called_once()



def test_firebase_notify_passanger_boarded_sends_fcm():
    """notify_passanger_boarded deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="presente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_boarded(tp)
        mock_send.assert_called_once()



def test_firebase_notify_passanger_absent_sends_fcm():
    """notify_passanger_absent deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="ausente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_absent(tp)
        mock_send.assert_called_once()



def test_firebase_notify_passanger_accepted_sends_fcm():
    """notify_passanger_accepted deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_accepted(rp)
        mock_send.assert_called_once()


def test_firebase_notify_passanger_rejected_sends_fcm():
    """notify_passanger_rejected deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_rejected(rp)
        mock_send.assert_called_once()


def test_firebase_notify_passanger_removed_sends_fcm():
    """notify_passanger_removed deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_removed(rp)
        mock_send.assert_called_once()


def test_firebase_notify_driver_passanger_requested_sends_fcm():
    """notify_driver_passanger_requested deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="pending")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_requested(rp)
        mock_send.assert_called_once()


def test_firebase_notify_driver_passanger_left_sends_fcm():
    """notify_driver_passanger_left deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_left(rp)
        mock_send.assert_called_once()


def test_firebase_notify_passanger_route_cancelled_sends_fcm():
    """notify_passanger_route_cancelled deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_route_cancelled(rp)
        mock_send.assert_called_once()


# ===========================================================================
# US12-TK03 fix — métodos faltantes (notify_trip_arrived_at_stop,
#                  notify_driver_passanger_absence_reported,
#                  notify_passanger_driver_approaching, notify_passanger_driver_arrived)
# ===========================================================================


def test_firebase_notify_trip_arrived_at_stop_sends_fcm():
    """notify_trip_arrived_at_stop deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="pendente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_arrived_at_stop(tp)
        mock_send.assert_called_once()


def test_firebase_notify_driver_passanger_absence_reported_sends_fcm():
    """notify_driver_passanger_absence_reported deve chamar firebase_admin.messaging.send."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_absence_reported(rp)
        mock_send.assert_called_once()


def test_firebase_notify_passanger_driver_approaching_sends_fcm():
    """notify_passanger_driver_approaching deve chamar firebase_admin.messaging.send via topic."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    user_id = str(uuid.uuid4())

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_driver_approaching(user_id, str(uuid.uuid4()))
        mock_send.assert_called_once()


def test_firebase_notify_passanger_driver_arrived_sends_fcm():
    """notify_passanger_driver_arrived deve chamar firebase_admin.messaging.send via topic."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    user_id = str(uuid.uuid4())

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_driver_arrived(user_id, str(uuid.uuid4()))
        mock_send.assert_called_once()


# ===========================================================================
# US12-TK13 — payload `data` estruturado em todas as notificações FCM
#
# Cada notificação precisa enviar um dict `data` no messaging.Message com:
#   - "type":      string fixa correspondente ao evento (vide tabela abaixo)
#   - "routeId":   str(uuid) da rota relacionada
#   - "passengerId": str(uuid) do route_passanger relacionado, quando faz
#                  sentido (eventos vinculados a um vínculo específico);
#                  "" para eventos de viagem inteira sem passageiro alvo
#
# Valores precisam ser STRING (FCM rejeita None / não-string em data).
# UUIDs devem ser convertidos via str().
#
# Os types abaixo são os mesmos do enum NotificationType do frontend
# (vango-frontend/types/notification.types.ts). Quem implementar a TK
# deve garantir que cada string bate exatamente com o valor do enum
# pra o roteamento no FE funcionar.
# ===========================================================================


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_trip_started_data_payload():
    """notify_trip_started deve incluir data={type:'trip_started', routeId, passengerId:''}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    trip = _make_trip_stub(status="iniciada")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_started(trip)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_started"
        assert message.data.get("routeId") == str(trip.route_id)
        assert message.data.get("passengerId", "") == ""


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_trip_arriving_at_stop_data_payload():
    """notify_trip_arriving_at_stop deve incluir data={type:'trip_arriving', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="pendente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_arriving_at_stop(tp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_arriving"
        assert message.data.get("routeId") == str(tp.route_passanger.route_id)
        assert message.data.get("passengerId") == str(tp.route_passanger_id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_trip_arrived_at_stop_data_payload():
    """notify_trip_arrived_at_stop deve incluir data={type:'trip_arrived', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="pendente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_arrived_at_stop(tp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_arrived"
        assert message.data.get("routeId") == str(tp.route_passanger.route_id)
        assert message.data.get("passengerId") == str(tp.route_passanger_id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_trip_finished_data_payload():
    """notify_trip_finished deve incluir data={type:'trip_finished', routeId, passengerId:''}.

    NOTE: 'trip_finished' ainda não está no enum NotificationType do
    frontend — o FE cai no fallback (home) quando receber. Backend deve
    enviar mesmo assim pra ficar forward-compatible.
    """
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    trip = _make_trip_stub(status="finalizada")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_finished(trip)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_finished"
        assert message.data.get("routeId") == str(trip.route_id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_boarded_data_payload():
    """notify_passanger_boarded deve incluir data={type:'passenger_boarded', routeId, passengerId}.

    NOTE: 'passenger_boarded' ainda não está no enum NotificationType do
    frontend — fallback até o FE adicionar.
    """
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="presente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_boarded(tp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "passenger_boarded"
        assert message.data.get("routeId") == str(tp.route_passanger.route_id)
        assert message.data.get("passengerId") == str(tp.route_passanger_id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_absent_data_payload():
    """notify_passanger_absent deve incluir data={type:'passenger_absent', routeId, passengerId}.

    NOTE: 'passenger_absent' ainda não está no enum NotificationType do
    frontend — fallback até o FE adicionar.
    """
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    tp = _make_trip_passanger_stub(status="ausente")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_absent(tp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "passenger_absent"
        assert message.data.get("routeId") == str(tp.route_passanger.route_id)
        assert message.data.get("passengerId") == str(tp.route_passanger_id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_accepted_data_payload():
    """notify_passanger_accepted deve incluir data={type:'passenger_accepted', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_accepted(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "passenger_accepted"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_rejected_data_payload():
    """notify_passanger_rejected deve incluir data={type:'passenger_rejected', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_rejected(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "passenger_rejected"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_removed_data_payload():
    """notify_passanger_removed deve incluir data={type:'passenger_removed', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_removed(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "passenger_removed"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_driver_passanger_requested_data_payload():
    """notify_driver_passanger_requested deve incluir data={type:'driver_passenger_requested', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="pending")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_requested(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "driver_passenger_requested"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_driver_passanger_left_data_payload():
    """notify_driver_passanger_left deve incluir data={type:'driver_passenger_left', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="rejected")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_left(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "driver_passenger_left"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_driver_passanger_absence_reported_data_payload():
    """notify_driver_passanger_absence_reported deve incluir data={type:'driver_passenger_absent', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_driver_passanger_absence_reported(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "driver_passenger_absent"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_route_cancelled_data_payload():
    """notify_passanger_route_cancelled deve incluir data={type:'route_cancelled', routeId, passengerId}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    rp = _make_rp_stub(status="accepted")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_route_cancelled(rp)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "route_cancelled"
        assert message.data.get("routeId") == str(rp.route_id)
        assert message.data.get("passengerId") == str(rp.id)


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_driver_approaching_data_payload():
    """notify_passanger_driver_approaching deve incluir data={type:'trip_arriving', routeId, passengerId:''}.

    Esse método não recebe um route_passanger model — apenas user_id e
    route_id como string. passengerId fica vazio.
    """
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    user_id = str(uuid.uuid4())
    route_id = str(uuid.uuid4())

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_driver_approaching(user_id, route_id)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_arriving"
        assert message.data.get("routeId") == route_id
        assert message.data.get("passengerId", "") == ""


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_passanger_driver_arrived_data_payload():
    """notify_passanger_driver_arrived deve incluir data={type:'trip_arrived', routeId, passengerId:''}."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    user_id = str(uuid.uuid4())
    route_id = str(uuid.uuid4())

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_passanger_driver_arrived(user_id, route_id)
        message = _sent_message(mock_send)
        assert message.data is not None
        assert message.data.get("type") == "trip_arrived"
        assert message.data.get("routeId") == route_id
        assert message.data.get("passengerId", "") == ""


@pytest.mark.skip(reason="US12-TK13")
def test_firebase_notify_data_values_are_all_strings():
    """Sanidade: TODOS os valores do dict `data` enviado ao FCM devem ser strings.

    FCM rejeita data com valor None ou tipos não-string em runtime; o teste
    pega isso direto inspecionando um exemplo (trip_started serve)."""
    from src.infrastructure.notifications.firebase_notification_service import (
        FirebaseNotificationService,
    )

    service = FirebaseNotificationService()
    trip = _make_trip_stub(status="iniciada")

    with patch("firebase_admin.messaging.send") as mock_send:
        service.notify_trip_started(trip)
        message = _sent_message(mock_send)
        assert message.data is not None
        for k, v in message.data.items():
            assert isinstance(k, str), f"chave {k!r} não é string"
            assert isinstance(v, str), f"valor de {k!r} = {v!r} não é string"
