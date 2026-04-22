"""US06-TK19 — Testes do AbsenceService.create_absence.

Cobre:
- criação bem-sucedida (self) e via guardian (dependent_id)
- 404 se rota não existir
- 403 se user não tiver vínculo ativo com a rota
- 409 se já existir ausência pro mesmo RP na data
- 409 se a data estiver fora da recorrência / no passado
- notificação do motorista
- persistência via repo.save
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_route_mock(driver_id: uuid.UUID, status: str = "ativa", recurrence: str = "seg,ter,qua,qui,sex"):
    from src.domains.routes.entity import RouteModel

    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.driver_id = driver_id
    route.status = status
    route.recurrence = recurrence
    return route


def make_rp_mock(route_id: uuid.UUID, user_id: uuid.UUID, dependent_id=None, status: str = "accepted"):
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id
    rp.user_id = user_id
    rp.dependent_id = dependent_id
    rp.status = status
    return rp


def build_service(**overrides):
    from src.domains.absences.service import AbsenceService
    from src.domains.notifications.service import INotificationService
    from src.domains.route_passangers.repository import IRoutePassangerRepository
    from src.domains.routes.repository import IRouteRepository
    from src.domains.trips.repository import IAbsenceRepository

    deps = {
        "absence_repository": Mock(spec=IAbsenceRepository),
        "route_repository": Mock(spec=IRouteRepository),
        "route_passanger_repository": Mock(spec=IRoutePassangerRepository),
        "notification_service": Mock(spec=INotificationService),
    }
    deps.update(overrides)
    return AbsenceService(**deps), deps


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_success_persists_and_notifies() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.trips.entity import AbsenceModel

    user_id = uuid.uuid4()
    driver_id = uuid.uuid4()

    service, deps = build_service()
    route = make_route_mock(driver_id=driver_id)
    rp = make_rp_mock(route_id=route.id, user_id=user_id)

    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = rp
    deps["absence_repository"].find_for_route_passanger_on_date.return_value = None
    saved = Mock(spec=AbsenceModel)
    saved.id = uuid.uuid4()
    saved.route_passanger_id = rp.id
    saved.absence_date = datetime(2026, 4, 27, 0, 0, tzinfo=timezone.utc)
    saved.reason = "Consulta"
    saved.created_at = datetime.now(tz=timezone.utc)
    deps["absence_repository"].save.return_value = saved

    req = CreateAbsenceRequest(
        route_id=route.id,
        absence_date=date(2026, 4, 27),
        reason="Consulta",
    )
    result = service.create_absence(user_id=user_id, data=req)

    deps["absence_repository"].save.assert_called_once()
    deps["notification_service"].notify_driver_passanger_absence_reported.assert_called_once_with(rp)
    assert result.id == saved.id


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_guardian_for_dependent_uses_dependent_rp() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest

    guardian_id = uuid.uuid4()
    dependent_id = uuid.uuid4()

    service, deps = build_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    rp = make_rp_mock(route_id=route.id, user_id=guardian_id, dependent_id=dependent_id)

    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = rp
    deps["absence_repository"].find_for_route_passanger_on_date.return_value = None

    req = CreateAbsenceRequest(
        route_id=route.id,
        absence_date=date(2026, 4, 27),
        dependent_id=dependent_id,
    )
    service.create_absence(user_id=guardian_id, data=req)

    call = deps["route_passanger_repository"].find_active_by_user_and_route.call_args
    # o service precisa passar o dependent_id pro repo
    assert dependent_id in call.args or call.kwargs.get("dependent_id") == dependent_id


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_route_not_found_raises_404() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.routes.errors import RouteNotFoundError

    service, deps = build_service()
    deps["route_repository"].find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=uuid.uuid4(),
                absence_date=date(2026, 4, 27),
            ),
        )


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_no_active_membership_raises_403() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.route_passangers.errors import NotRoutePassangerError

    service, deps = build_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = None

    with pytest.raises(NotRoutePassangerError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=route.id,
                absence_date=date(2026, 4, 27),
            ),
        )


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_duplicate_raises_409() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.absences.errors import AbsenceAlreadyReportedError
    from src.domains.trips.entity import AbsenceModel

    service, deps = build_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    rp = make_rp_mock(route_id=route.id, user_id=uuid.uuid4())

    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = rp
    existing = Mock(spec=AbsenceModel)
    deps["absence_repository"].find_for_route_passanger_on_date.return_value = existing

    with pytest.raises(AbsenceAlreadyReportedError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=route.id,
                absence_date=date(2026, 4, 27),
            ),
        )


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_past_date_raises_409() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.absences.errors import AbsenceDateNotAllowedError

    service, deps = build_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    rp = make_rp_mock(route_id=route.id, user_id=uuid.uuid4())

    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = rp

    with pytest.raises(AbsenceDateNotAllowedError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=route.id,
                absence_date=date(2020, 1, 1),
            ),
        )


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_date_not_in_route_recurrence_raises_409() -> None:
    """Se a rota só roda seg-sex e o passageiro avisa ausência num sábado,
    bloqueia."""
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.absences.errors import AbsenceDateNotAllowedError

    service, deps = build_service()
    # rota só roda segunda e quarta
    route = make_route_mock(driver_id=uuid.uuid4(), recurrence="seg,qua")
    rp = make_rp_mock(route_id=route.id, user_id=uuid.uuid4())

    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = rp

    # 25/04/2026 é um sábado → fora da recorrência
    with pytest.raises(AbsenceDateNotAllowedError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=route.id,
                absence_date=date(2026, 4, 25),
            ),
        )


@pytest.mark.skip(reason="US06-TK19")
def test_create_absence_does_not_notify_on_validation_error() -> None:
    from src.domains.absences.dtos import CreateAbsenceRequest
    from src.domains.route_passangers.errors import NotRoutePassangerError

    service, deps = build_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    deps["route_repository"].find_by_id.return_value = route
    deps["route_passanger_repository"].find_active_by_user_and_route.return_value = None

    with pytest.raises(NotRoutePassangerError):
        service.create_absence(
            user_id=uuid.uuid4(),
            data=CreateAbsenceRequest(
                route_id=route.id,
                absence_date=date(2026, 4, 27),
            ),
        )

    deps["notification_service"].notify_driver_passanger_absence_reported.assert_not_called()
    deps["absence_repository"].save.assert_not_called()
