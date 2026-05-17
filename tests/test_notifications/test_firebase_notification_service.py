"""US12-TK03 / TK04 — Testes de FirebaseNotificationService.

TK03: verifica que a classe existe, implementa INotificationService, e que
      get_firebase_notification_service retorna uma instância válida.
TK04: verifica que cada método FCM envia a mensagem correta via Admin SDK.
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
# US12-TK04 — métodos FCM de execução de viagem
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
