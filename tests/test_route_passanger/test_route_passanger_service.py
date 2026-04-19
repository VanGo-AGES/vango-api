import uuid
from unittest.mock import Mock

import pytest

# ===========================================================================
# US06 — RoutePassangerService
# Arquivo: src/domains/route_passangers/service.py
#
# TK08: accept_request
# TK10: reject_request
# TK12: remove_passanger
# TK14: list_by_status
#
# Todas as operações exigem:
#   - driver dono da rota (403 se não for)
#   - rota não pode estar 'em_andamento' (409 RouteInProgressError)
# Accept/Reject só operam em status='pending'.
# Accept ainda valida capacidade máxima (count_accepted < max_passengers).
# ===========================================================================


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_route_mock(driver_id: uuid.UUID, status: str = "ativa", max_passengers: int = 5):
    from src.domains.routes.entity import RouteModel

    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.driver_id = driver_id
    route.status = status
    route.max_passengers = max_passengers
    return route


def make_rp_mock(route_id: uuid.UUID, user_id: uuid.UUID, status: str = "pending", dependent_id=None):
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id
    rp.user_id = user_id
    rp.dependent_id = dependent_id
    rp.status = status
    rp.joined_at = None
    return rp


def make_user_mock(name: str = "Usuário"):
    from src.domains.users.entity import UserModel

    user = Mock(spec=UserModel)
    user.id = uuid.uuid4()
    user.name = name
    return user


def make_dependent_mock(name: str = "Dependente", guardian_id=None):
    from src.domains.dependents.entity import DependentModel

    dep = Mock(spec=DependentModel)
    dep.id = uuid.uuid4()
    dep.name = name
    dep.guardian_id = guardian_id or uuid.uuid4()
    return dep


def build_service(**overrides):
    from src.domains.route_passangers.service import RoutePassangerService

    rp_repo = overrides.pop("rp_repo", Mock())
    route_repo = overrides.pop("route_repo", Mock())
    user_repo = overrides.pop("user_repo", Mock())
    dep_repo = overrides.pop("dep_repo", Mock())
    notif = overrides.pop("notif", Mock())
    return RoutePassangerService(rp_repo, route_repo, user_repo, dep_repo, notif), rp_repo, route_repo, user_repo, dep_repo, notif


# ===========================================================================
# TK08 — accept_request
# ===========================================================================


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_success_returns_response() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=5)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    user = make_user_mock("João")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    updated = make_rp_mock(route.id, rp.user_id, status="accepted")
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = user

    response = service.accept_request(route.id, rp.id, driver_id)

    assert response.status == "accepted"


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_calls_update_status_accepted() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()

    service.accept_request(route.id, rp.id, driver_id)

    rp_repo.update_status.assert_called_once_with(rp.id, "accepted")


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_notifies_accepted() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    updated = make_rp_mock(route.id, rp.user_id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, notif = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = make_user_mock()

    service.accept_request(route.id, rp.id, driver_id)

    notif.notify_passanger_accepted.assert_called_once()


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.accept_request(uuid.uuid4(), uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    other_driver = uuid.uuid4()
    route = make_route_mock(other_driver, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    with pytest.raises(RouteOwnershipError):
        service.accept_request(route.id, uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_route_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.accept_request(route.id, rp.id, driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_rp_not_found_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.accept_request(route.id, uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_already_processed_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RoutePassangerAlreadyProcessedError):
        service.accept_request(route.id, rp.id, driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_capacity_exceeded_raises() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=2)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 2

    with pytest.raises(RouteCapacityExceededError):
        service.accept_request(route.id, rp.id, driver_id)


@pytest.mark.skip(reason="US06-TK08")
def test_accept_request_capacity_at_limit_blocks() -> None:
    """count==max_passengers já deve bloquear."""
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=3)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 3

    with pytest.raises(RouteCapacityExceededError):
        service.accept_request(route.id, rp.id, driver_id)


# ===========================================================================
# TK10 — reject_request
# ===========================================================================


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_success_returns_response() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    updated = make_rp_mock(route.id, rp.user_id, status="rejected")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = make_user_mock()

    response = service.reject_request(route.id, rp.id, driver_id)

    assert response.status == "rejected"


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_calls_update_status_rejected() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    rp_repo.update_status.assert_called_once_with(rp.id, "rejected")


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_notifies_rejected() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, notif = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    notif.notify_passanger_rejected.assert_called_once()


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.reject_request(route.id, rp.id, driver_id)


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_already_processed_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="rejected")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RoutePassangerAlreadyProcessedError):
        service.reject_request(route.id, rp.id, driver_id)


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    other = uuid.uuid4()
    route = make_route_mock(other, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    with pytest.raises(RouteOwnershipError):
        service.reject_request(route.id, uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK10")
def test_reject_request_does_not_check_capacity() -> None:
    """Reject não deve chamar count_accepted_by_route."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=1)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    rp_repo.count_accepted_by_route.assert_not_called()


# ===========================================================================
# TK12 — remove_passanger
# ===========================================================================


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_success_returns_none() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    result = service.remove_passanger(route.id, rp.id, driver_id)

    assert result is None


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_calls_delete() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    service.remove_passanger(route.id, rp.id, driver_id)

    rp_repo.delete.assert_called_once_with(rp.id)


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_notifies_before_delete() -> None:
    """Notify deve ser chamado antes de delete (objeto rp ainda existe)."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, notif = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    service.remove_passanger(route.id, rp.id, driver_id)

    notif.notify_passanger_removed.assert_called_once_with(rp)


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.remove_passanger(uuid.uuid4(), uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    route = make_route_mock(uuid.uuid4(), status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    with pytest.raises(RouteOwnershipError):
        service.remove_passanger(route.id, uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_rp_not_found_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.remove_passanger(route.id, uuid.uuid4(), driver_id)


@pytest.mark.skip(reason="US06-TK12")
def test_remove_passanger_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.remove_passanger(route.id, rp.id, driver_id)


# ===========================================================================
# TK14 — list_by_status
# ===========================================================================


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_returns_responses() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp1 = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    rp2 = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp1, rp2]
    user_repo.find_by_id.return_value = make_user_mock()

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert len(result) == 2


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_filters_via_repository() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    service.list_by_status(route.id, driver_id, status="pending")

    rp_repo.find_by_route_and_status.assert_called_once_with(route.id, "pending")


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_no_filter_passes_none() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    service.list_by_status(route.id, driver_id, status=None)

    rp_repo.find_by_route_and_status.assert_called_once_with(route.id, None)


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.list_by_status(uuid.uuid4(), driver_id, status="pending")


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    route = make_route_mock(uuid.uuid4(), status="ativa")

    service, _, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route

    with pytest.raises(RouteOwnershipError):
        service.list_by_status(route.id, driver_id, status="pending")


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_invalid_status_raises_value_error() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, _, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route

    with pytest.raises(ValueError):
        service.list_by_status(route.id, driver_id, status="invalid_status")


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_empty_list_returned() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result == []


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_resolves_user_name() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    user = make_user_mock("Maria")
    rp = make_rp_mock(route.id, user.id, status="pending")

    service, rp_repo, route_repo, user_repo, _, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp]
    user_repo.find_by_id.return_value = user

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result[0].user_name == "Maria"


@pytest.mark.skip(reason="US06-TK14")
def test_list_by_status_resolves_dependent_and_guardian_names() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    guardian = make_user_mock("Responsável João")
    dependent = make_dependent_mock("Filha Ana", guardian_id=guardian.id)
    rp = make_rp_mock(route.id, guardian.id, status="pending", dependent_id=dependent.id)

    service, rp_repo, route_repo, user_repo, dep_repo, _ = build_service()
    route_repo.get_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp]
    user_repo.find_by_id.return_value = guardian
    dep_repo.get_by_id.return_value = dependent

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result[0].dependent_name == "Filha Ana"
    assert result[0].guardian_name == "Responsável João"
