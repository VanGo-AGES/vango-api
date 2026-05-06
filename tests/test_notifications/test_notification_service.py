import uuid
from unittest.mock import Mock

import pytest

# ===========================================================================
# US06 - TK07: INotificationService + LoggingNotificationService
# Arquivo:     src/domains/notifications/service.py
# Critérios:   Interface expõe notify_passanger_accepted/rejected/removed.
#              LoggingNotificationService implementa a interface e não
#              levanta exceções quando chamada.
# ===========================================================================


def make_rp_stub(status: str = "pending"):
    """Stub leve de RoutePassangerModel para verificação por spec."""
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = uuid.uuid4()
    rp.user_id = uuid.uuid4()
    rp.dependent_id = None
    rp.status = status
    return rp


@pytest.mark.skip(reason="US06-TK07")
def test_notification_service_is_abstract() -> None:
    from src.domains.notifications.service import INotificationService

    with pytest.raises(TypeError):
        INotificationService()  # type: ignore[abstract]


@pytest.mark.skip(reason="US06-TK07")
def test_logging_notification_service_implements_interface() -> None:
    from src.domains.notifications.service import INotificationService, LoggingNotificationService

    service = LoggingNotificationService()
    assert isinstance(service, INotificationService)


@pytest.mark.skip(reason="US06-TK07")
def test_logging_notification_service_notify_accepted_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="accepted")
    # Não deve levantar nem retornar valor (retorna None)
    assert service.notify_passanger_accepted(rp) is None


@pytest.mark.skip(reason="US06-TK07")
def test_logging_notification_service_notify_rejected_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="rejected")
    assert service.notify_passanger_rejected(rp) is None


@pytest.mark.skip(reason="US06-TK07")
def test_logging_notification_service_notify_removed_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="accepted")
    assert service.notify_passanger_removed(rp) is None


@pytest.mark.skip(reason="US06-TK07")
def test_notification_service_methods_signature() -> None:
    """Valida que métodos esperados existem na interface."""
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_passanger_accepted")
    assert hasattr(INotificationService, "notify_passanger_rejected")
    assert hasattr(INotificationService, "notify_passanger_removed")


# ===========================================================================
# US08-TK04 — eventos originados pelo passageiro
# ===========================================================================


@pytest.mark.skip(reason="US08-TK04")
def test_notification_service_passanger_events_in_interface() -> None:
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_driver_passanger_requested")
    assert hasattr(INotificationService, "notify_driver_passanger_left")
    assert hasattr(INotificationService, "notify_driver_passanger_schedules_changed")


@pytest.mark.skip(reason="US08-TK04")
def test_logging_notify_driver_requested_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="pending")
    assert service.notify_driver_passanger_requested(rp) is None


@pytest.mark.skip(reason="US08-TK04")
def test_logging_notify_driver_left_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="accepted")
    assert service.notify_driver_passanger_left(rp) is None


@pytest.mark.skip(reason="US08-TK04")
def test_logging_notify_driver_schedules_changed_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="accepted")
    assert service.notify_driver_passanger_schedules_changed(rp) is None


# ===========================================================================
# US06-TK16 — evento de exclusão da rota
# ===========================================================================


def test_notification_service_route_cancelled_in_interface() -> None:
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_passanger_route_cancelled")


def test_logging_notify_passanger_route_cancelled_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="accepted")
    assert service.notify_passanger_route_cancelled(rp) is None


def test_logging_notify_passanger_route_cancelled_pending_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    rp = make_rp_stub(status="pending")
    assert service.notify_passanger_route_cancelled(rp) is None


# ===========================================================================
# US09-TK05 — eventos de execução de viagem
# ===========================================================================


def make_trip_stub(status: str = "iniciada"):
    from src.domains.trips.entity import TripModel

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.route_id = uuid.uuid4()
    trip.vehicle_id = uuid.uuid4()
    trip.status = status
    return trip


def make_trip_passanger_stub(status: str = "pendente"):
    from src.domains.trips.entity import TripPassangerModel

    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = uuid.uuid4()
    tp.route_passanger_id = uuid.uuid4()
    tp.status = status
    return tp


def test_notification_service_trip_events_in_interface() -> None:
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_trip_started")
    assert hasattr(INotificationService, "notify_trip_arriving_at_stop")
    assert hasattr(INotificationService, "notify_trip_finished")


def test_logging_notify_trip_started_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    trip = make_trip_stub(status="iniciada")
    assert service.notify_trip_started(trip) is None


def test_logging_notify_trip_arriving_at_stop_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    tp = make_trip_passanger_stub(status="pendente")
    assert service.notify_trip_arriving_at_stop(tp) is None


def test_logging_notify_trip_finished_does_not_raise() -> None:
    from src.domains.notifications.service import LoggingNotificationService

    service = LoggingNotificationService()
    trip = make_trip_stub(status="finalizada")
    assert service.notify_trip_finished(trip) is None
