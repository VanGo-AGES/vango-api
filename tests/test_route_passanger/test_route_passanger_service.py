import uuid
from unittest.mock import MagicMock, Mock

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


def make_route_mock(driver_id: uuid.UUID, status: str = "ativa", max_passengers: int = 5, route_type: str = "outbound"):
    from src.domains.routes.entity import RouteModel

    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.driver_id = driver_id
    route.status = status
    route.max_passengers = max_passengers
    route.route_type = route_type
    return route


def make_rp_mock(
    route_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str = "pending",
    dependent_id=None,
    pickup_address_id=None,
):
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id
    rp.user_id = user_id
    rp.dependent_id = dependent_id
    rp.pickup_address_id = pickup_address_id or uuid.uuid4()
    rp.status = status
    rp.joined_at = None
    return rp


def make_user_mock(name: str = "Usuário", phone: str = "51999999999"):
    from src.domains.users.entity import UserModel

    user = Mock(spec=UserModel)
    user.id = uuid.uuid4()
    user.name = name
    user.phone = phone
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
    stop_repo = overrides.pop("stop_repo", Mock())
    schedule_repo = overrides.pop("schedule_repo", Mock())
    return (
        RoutePassangerService(
            rp_repo, route_repo, user_repo, dep_repo, notif, stop_repo, schedule_repo
        ),
        rp_repo,
        route_repo,
        user_repo,
        dep_repo,
        notif,
        stop_repo,
        schedule_repo,
    )


# ===========================================================================
# TK08 — accept_request
# ===========================================================================


def test_accept_request_success_returns_response() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=5)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    user = make_user_mock("João")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    updated = make_rp_mock(route.id, rp.user_id, status="accepted")
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = user

    response = service.accept_request(route.id, rp.id, driver_id)

    assert response.status == "accepted"


def test_accept_request_calls_update_status_accepted() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()

    service.accept_request(route.id, rp.id, driver_id)

    rp_repo.update_status.assert_called_once_with(rp.id, "accepted")


def test_accept_request_notifies_accepted() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    updated = make_rp_mock(route.id, rp.user_id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, notif, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = make_user_mock()

    service.accept_request(route.id, rp.id, driver_id)

    notif.notify_passanger_accepted.assert_called_once()


def test_accept_request_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.accept_request(uuid.uuid4(), uuid.uuid4(), driver_id)


def test_accept_request_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    other_driver = uuid.uuid4()
    route = make_route_mock(other_driver, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    with pytest.raises(RouteOwnershipError):
        service.accept_request(route.id, uuid.uuid4(), driver_id)


def test_accept_request_route_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.accept_request(route.id, rp.id, driver_id)


def test_accept_request_rp_not_found_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.accept_request(route.id, uuid.uuid4(), driver_id)


def test_accept_request_already_processed_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RoutePassangerAlreadyProcessedError):
        service.accept_request(route.id, rp.id, driver_id)


def test_accept_request_capacity_exceeded_raises() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=2)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 2

    with pytest.raises(RouteCapacityExceededError):
        service.accept_request(route.id, rp.id, driver_id)


def test_accept_request_capacity_at_limit_blocks() -> None:
    """count==max_passengers já deve bloquear."""
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=3)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 3

    with pytest.raises(RouteCapacityExceededError):
        service.accept_request(route.id, rp.id, driver_id)


# ---------------------------------------------------------------------------
# TK08 — accept_request deve criar Stop vinculada ao passageiro
# ---------------------------------------------------------------------------


def test_accept_request_creates_stop_via_stop_repository() -> None:
    """accept_request deve chamar stop_repository.save com a Stop do passageiro."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    stop_repo.save.assert_called_once()


def test_accept_request_stop_uses_rp_pickup_address_id() -> None:
    """A Stop criada deve usar o pickup_address_id do passageiro."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    pickup = uuid.uuid4()
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending", pickup_address_id=pickup)

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.address_id == pickup


def test_accept_request_stop_type_embarque_for_outbound_route() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.type == "embarque"


def test_accept_request_stop_type_desembarque_for_inbound_route() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="inbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.type == "desembarque"


def test_accept_request_stop_order_index_is_zero_when_no_stops() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.order_index == 0


def test_accept_request_stop_order_index_is_max_plus_one() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    existing_a = Mock()
    existing_a.order_index = 0
    existing_b = Mock()
    existing_b.order_index = 3

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = [existing_a, existing_b]

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.order_index == 4


def test_accept_request_stop_links_to_route_and_rp() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", route_type="outbound")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.count_accepted_by_route.return_value = 0
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="accepted")
    user_repo.find_by_id.return_value = make_user_mock()
    stop_repo.find_by_route_id.return_value = []

    service.accept_request(route.id, rp.id, driver_id)

    saved_stop = stop_repo.save.call_args[0][0]
    assert saved_stop.route_id == route.id
    assert saved_stop.route_passanger_id == rp.id


# ===========================================================================
# TK10 — reject_request
# ===========================================================================


def test_reject_request_success_returns_response() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    updated = make_rp_mock(route.id, rp.user_id, status="rejected")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = updated
    user_repo.find_by_id.return_value = make_user_mock()

    response = service.reject_request(route.id, rp.id, driver_id)

    assert response.status == "rejected"


def test_reject_request_calls_update_status_rejected() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    rp_repo.update_status.assert_called_once_with(rp.id, "rejected")


def test_reject_request_notifies_rejected() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, notif, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    notif.notify_passanger_rejected.assert_called_once()


def test_reject_request_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.reject_request(route.id, rp.id, driver_id)


def test_reject_request_already_processed_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="rejected")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RoutePassangerAlreadyProcessedError):
        service.reject_request(route.id, rp.id, driver_id)


def test_reject_request_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    other = uuid.uuid4()
    route = make_route_mock(other, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    with pytest.raises(RouteOwnershipError):
        service.reject_request(route.id, uuid.uuid4(), driver_id)


def test_reject_request_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.reject_request(uuid.uuid4(), uuid.uuid4(), driver_id)


def test_reject_request_rp_not_found_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.reject_request(route.id, uuid.uuid4(), driver_id)


def test_reject_request_does_not_check_capacity() -> None:
    """Reject não deve chamar count_accepted_by_route."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa", max_passengers=1)
    rp = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.update_status.return_value = make_rp_mock(route.id, rp.user_id, status="rejected")
    user_repo.find_by_id.return_value = make_user_mock()

    service.reject_request(route.id, rp.id, driver_id)

    rp_repo.count_accepted_by_route.assert_not_called()


# ===========================================================================
# TK12 — remove_passanger
# ===========================================================================


def test_remove_passanger_success_returns_none() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    result = service.remove_passanger(route.id, rp.id, driver_id)

    assert result is None


def test_remove_passanger_calls_delete() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    service.remove_passanger(route.id, rp.id, driver_id)

    rp_repo.delete.assert_called_once_with(rp.id)


def test_remove_passanger_notifies_before_delete() -> None:
    """Notify deve ser chamado antes de delete (objeto rp ainda existe)."""
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, notif, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    service.remove_passanger(route.id, rp.id, driver_id)

    notif.notify_passanger_removed.assert_called_once_with(rp)


def test_remove_passanger_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.remove_passanger(uuid.uuid4(), uuid.uuid4(), driver_id)


def test_remove_passanger_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    route = make_route_mock(uuid.uuid4(), status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    with pytest.raises(RouteOwnershipError):
        service.remove_passanger(route.id, uuid.uuid4(), driver_id)


def test_remove_passanger_rp_not_found_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.remove_passanger(route.id, uuid.uuid4(), driver_id)


def test_remove_passanger_in_progress_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="em_andamento")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp

    with pytest.raises(RouteInProgressError):
        service.remove_passanger(route.id, rp.id, driver_id)


# ---------------------------------------------------------------------------
# TK12 — remove_passanger deve remover Stop vinculada
# ---------------------------------------------------------------------------


def test_remove_passanger_deletes_stop_by_rp_id() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    service, rp_repo, route_repo, _, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    service.remove_passanger(route.id, rp.id, driver_id)

    stop_repo.delete_by_route_passanger_id.assert_called_once_with(rp.id)


def test_remove_passanger_deletes_stop_before_rp_delete() -> None:
    """Stop deve ser deletada ANTES de rp_repo.delete (FK rp -> stop)."""
    from unittest.mock import MagicMock

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp = make_rp_mock(route.id, uuid.uuid4(), status="accepted")

    manager = MagicMock()
    service, rp_repo, route_repo, _, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_id.return_value = rp
    rp_repo.delete.return_value = True

    manager.attach_mock(stop_repo.delete_by_route_passanger_id, "stop_delete")
    manager.attach_mock(rp_repo.delete, "rp_delete")

    service.remove_passanger(route.id, rp.id, driver_id)

    call_names = [c[0] for c in manager.mock_calls]
    assert call_names.index("stop_delete") < call_names.index("rp_delete")


# ===========================================================================
# TK14 — list_by_status
# ===========================================================================


def test_list_by_status_returns_responses() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    rp1 = make_rp_mock(route.id, uuid.uuid4(), status="pending")
    rp2 = make_rp_mock(route.id, uuid.uuid4(), status="pending")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp1, rp2]
    user_repo.find_by_id.return_value = make_user_mock()

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert len(result) == 2


def test_list_by_status_filters_via_repository() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    service.list_by_status(route.id, driver_id, status="pending")

    rp_repo.find_by_route_and_status.assert_called_once_with(route.id, "pending")


def test_list_by_status_no_filter_passes_none() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    service.list_by_status(route.id, driver_id, status=None)

    rp_repo.find_by_route_and_status.assert_called_once_with(route.id, None)


def test_list_by_status_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    driver_id = uuid.uuid4()
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.list_by_status(uuid.uuid4(), driver_id, status="pending")


def test_list_by_status_wrong_owner_raises() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    driver_id = uuid.uuid4()
    route = make_route_mock(uuid.uuid4(), status="ativa")

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route

    with pytest.raises(RouteOwnershipError):
        service.list_by_status(route.id, driver_id, status="pending")


def test_list_by_status_invalid_status_raises_value_error() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route

    with pytest.raises(ValueError):
        service.list_by_status(route.id, driver_id, status="invalid_status")


def test_list_by_status_empty_list_returned() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = []

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result == []


def test_list_by_status_resolves_user_name() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    user = make_user_mock("Maria", phone="54988887777")
    rp = make_rp_mock(route.id, user.id, status="pending")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp]
    user_repo.find_by_id.return_value = user

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result[0].user_name == "Maria"
    # US13 — phone precisa estar no response pro FE montar deeplink de contato
    assert result[0].user_phone == "54988887777"


def test_list_by_status_resolves_dependent_and_guardian_names() -> None:
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id, status="ativa")
    guardian = make_user_mock("Responsável João")
    dependent = make_dependent_mock("Filha Ana", guardian_id=guardian.id)
    rp = make_rp_mock(route.id, guardian.id, status="pending", dependent_id=dependent.id)

    service, rp_repo, route_repo, user_repo, dep_repo, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_by_route_and_status.return_value = [rp]
    user_repo.find_by_id.return_value = guardian
    dep_repo.get_by_id.return_value = dependent

    result = service.list_by_status(route.id, driver_id, status="pending")

    assert result[0].dependent_name == "Filha Ana"
    assert result[0].guardian_name == "Responsável João"



# ===========================================================================
# US08-TK07 — RoutePassangerService.join_route
# ===========================================================================


def make_join_request(dependent_id=None, days=("monday",), address_id=None):
    from src.domains.route_passangers.dtos import (
        JoinRouteRequest,
        RoutePassangerScheduleRequest,
    )

    address_id = address_id or uuid.uuid4()
    schedules = [
        RoutePassangerScheduleRequest(day_of_week=day, address_id=address_id)
        for day in days
    ]
    return JoinRouteRequest(dependent_id=dependent_id, schedules=schedules)


def test_join_route_success_creates_pending_rp() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa", max_passengers=5)
    user_id = uuid.uuid4()
    address_id = uuid.uuid4()
    req = make_join_request(days=("monday", "wednesday"), address_id=address_id)

    service, rp_repo, route_repo, _, _, _, _, schedule_repo = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None
    rp_repo.count_accepted_by_route.return_value = 0
    created = make_rp_mock(route.id, user_id, status="pending", pickup_address_id=address_id)
    rp_repo.save.return_value = created

    service.join_route(route.id, user_id, req)

    rp_repo.save.assert_called_once()
    schedule_repo.save_many.assert_called_once()


def test_join_route_pickup_address_equals_first_schedule() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    address_id = uuid.uuid4()
    req = make_join_request(days=("monday",), address_id=address_id)

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None
    rp_repo.count_accepted_by_route.return_value = 0

    service.join_route(route.id, user_id, req)

    saved_rp = rp_repo.save.call_args.args[0]
    assert saved_rp.pickup_address_id == address_id


def test_join_route_notifies_driver() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    service, rp_repo, route_repo, _, _, notif, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None
    rp_repo.count_accepted_by_route.return_value = 0

    service.join_route(route.id, uuid.uuid4(), make_join_request())

    notif.notify_driver_passanger_requested.assert_called_once()


def test_join_route_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.join_route(uuid.uuid4(), uuid.uuid4(), make_join_request())


def test_join_route_em_andamento_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    route = make_route_mock(uuid.uuid4(), status="em_andamento")
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route

    with pytest.raises(RouteInProgressError):
        service.join_route(route.id, uuid.uuid4(), make_join_request())


def test_join_route_full_capacity_raises() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    route = make_route_mock(uuid.uuid4(), status="ativa", max_passengers=2)
    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None
    rp_repo.count_accepted_by_route.return_value = 2

    with pytest.raises(RouteCapacityExceededError):
        service.join_route(route.id, uuid.uuid4(), make_join_request())


def test_join_route_duplicate_active_raises() -> None:
    from src.domains.route_passangers.errors import DuplicateRoutePassangerError

    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    existing = make_rp_mock(route.id, user_id, status="pending")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = existing

    with pytest.raises(DuplicateRoutePassangerError):
        service.join_route(route.id, user_id, make_join_request())


def test_join_route_rejected_previous_allows_new_request() -> None:
    """Ter um RP rejected anterior NÃO bloqueia — find_active retorna None."""
    route = make_route_mock(uuid.uuid4(), status="ativa")
    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None  # não há ativo
    rp_repo.count_accepted_by_route.return_value = 0

    service.join_route(route.id, uuid.uuid4(), make_join_request())

    rp_repo.save.assert_called_once()


def test_join_route_with_dependent_id_sets_dep_on_rp() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    guardian_id = uuid.uuid4()
    dep_id = uuid.uuid4()

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None
    rp_repo.count_accepted_by_route.return_value = 0

    service.join_route(route.id, guardian_id, make_join_request(dependent_id=dep_id))

    saved_rp = rp_repo.save.call_args.args[0]
    assert saved_rp.dependent_id == dep_id


# ===========================================================================
# US08-TK09 — RoutePassangerService.leave_route
# ===========================================================================


def test_leave_route_success_deletes_rp() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    rp = make_rp_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.leave_route(route.id, user_id)

    rp_repo.delete.assert_called_once_with(rp.id)


def test_leave_route_notifies_driver_before_delete() -> None:
    """Valida a ordem exata: notify vem antes de stop_repository.delete e de rp_repo.delete."""
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    rp = make_rp_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, _, _, notif, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    manager = MagicMock()
    manager.attach_mock(notif.notify_driver_passanger_left, "notify")
    manager.attach_mock(stop_repo.delete_by_route_passanger_id, "delete_stop")
    manager.attach_mock(rp_repo.delete, "delete_rp")

    service.leave_route(route.id, user_id)

    call_names = [c[0] for c in manager.mock_calls]
    assert call_names.index("notify") < call_names.index("delete_rp"), (
        f"notify deve vir antes do delete_rp, mas ordem foi: {call_names}"
    )
    if "delete_stop" in call_names:
        assert call_names.index("notify") < call_names.index("delete_stop"), (
            f"notify deve vir antes do delete_stop, mas ordem foi: {call_names}"
        )


def test_leave_route_deletes_stop_explicitly() -> None:
    """Valida que stop_repository.delete_by_route_passanger_id é chamado explicitamente,
    permitindo hooks (push notification, auditoria) que a cascade do ORM não dispararia."""
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    rp = make_rp_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, _, _, _, stop_repo, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.leave_route(route.id, user_id)

    stop_repo.delete_by_route_passanger_id.assert_called_once_with(rp.id)


def test_leave_route_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.leave_route(uuid.uuid4(), uuid.uuid4())


def test_leave_route_em_andamento_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    route = make_route_mock(uuid.uuid4(), status="em_andamento")
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route

    with pytest.raises(RouteInProgressError):
        service.leave_route(route.id, uuid.uuid4())


def test_leave_route_no_active_rp_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    route = make_route_mock(uuid.uuid4(), status="ativa")
    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.leave_route(route.id, uuid.uuid4())


def test_leave_route_with_dependent_id_uses_dependent_scope() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    guardian_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    rp = make_rp_mock(route.id, guardian_id, status="accepted", dependent_id=dep_id)

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.leave_route(route.id, guardian_id, dependent_id=dep_id)

    # find_active_by_user_and_route deve ter sido chamado com o dependent_id
    call_kwargs = rp_repo.find_active_by_user_and_route.call_args.kwargs
    call_args = rp_repo.find_active_by_user_and_route.call_args.args
    assert dep_id in call_args or call_kwargs.get("dependent_id") == dep_id


# ===========================================================================
# US08-TK11 — RoutePassangerService.update_schedules
# ===========================================================================


def make_update_request(days=("monday",), address_id=None):
    from src.domains.route_passangers.dtos import (
        RoutePassangerScheduleRequest,
        UpdateSchedulesRequest,
    )

    address_id = address_id or uuid.uuid4()
    schedules = [
        RoutePassangerScheduleRequest(day_of_week=day, address_id=address_id)
        for day in days
    ]
    return UpdateSchedulesRequest(schedules=schedules)


def test_update_schedules_success_replaces_schedules() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    rp = make_rp_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, _, _, _, _, schedule_repo = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.update_schedules(
        route.id,
        user_id,
        make_update_request(days=("monday", "wednesday", "friday")),
    )

    schedule_repo.replace.assert_called_once()


def test_update_schedules_notifies_driver() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user_id = uuid.uuid4()
    rp = make_rp_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, _, _, notif, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.update_schedules(route.id, user_id, make_update_request())

    notif.notify_driver_passanger_schedules_changed.assert_called_once()


def test_update_schedules_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.update_schedules(uuid.uuid4(), uuid.uuid4(), make_update_request())


def test_update_schedules_em_andamento_raises() -> None:
    from src.domains.routes.errors import RouteInProgressError

    route = make_route_mock(uuid.uuid4(), status="em_andamento")
    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route

    with pytest.raises(RouteInProgressError):
        service.update_schedules(route.id, uuid.uuid4(), make_update_request())


def test_update_schedules_no_active_rp_raises() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    route = make_route_mock(uuid.uuid4(), status="ativa")
    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None

    with pytest.raises(RoutePassangerNotFoundError):
        service.update_schedules(route.id, uuid.uuid4(), make_update_request())


def test_update_schedules_with_dependent_id_uses_dependent_scope() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    guardian_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    rp = make_rp_mock(route.id, guardian_id, status="accepted", dependent_id=dep_id)

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp

    service.update_schedules(
        route.id, guardian_id, make_update_request(), dependent_id=dep_id
    )

    call_kwargs = rp_repo.find_active_by_user_and_route.call_args.kwargs
    call_args = rp_repo.find_active_by_user_and_route.call_args.args
    assert dep_id in call_args or call_kwargs.get("dependent_id") == dep_id


def test_update_schedules_returns_response_with_resolved_names() -> None:
    route = make_route_mock(uuid.uuid4(), status="ativa")
    user = make_user_mock("Passageiro X", phone="54988887777")
    rp = make_rp_mock(route.id, user.id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = user

    result = service.update_schedules(route.id, user.id, make_update_request())

    assert result.user_name == "Passageiro X"
    # US13 — phone precisa estar no response pro driver contatar via deeplink
    assert result.user_phone == "54988887777"


# ===========================================================================
# US08-TK14 — list_my_routes
# Arquivo: src/domains/route_passangers/service.py
# ===========================================================================


def make_rp_with_route_mock(
    route_id: uuid.UUID,
    user_id: uuid.UUID,
    driver_id: uuid.UUID,
    status: str = "accepted",
    dependent_id=None,
    route_name: str = "PUCRS",
    route_status: str = "ativa",
    origin_label: str = "Casa",
    destination_label: str = "PUCRS",
):
    """RP mock com RouteModel (e endereços) já carregados, como vem do repo."""
    from datetime import time as dtime
    from src.domains.addresses.entity import AddressModel
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.domains.routes.entity import RouteModel

    origin = Mock(spec=AddressModel)
    origin.id = uuid.uuid4()
    origin.label = origin_label
    destination = Mock(spec=AddressModel)
    destination.id = uuid.uuid4()
    destination.label = destination_label

    route = Mock(spec=RouteModel)
    route.id = route_id
    route.name = route_name
    route.driver_id = driver_id
    route.status = route_status
    route.expected_time = dtime(8, 0)
    route.recurrence = "seg,ter,qua,qui,sex"
    route.origin = origin
    route.destination = destination
    route.origin_address_id = origin.id
    route.destination_address_id = destination.id

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id
    rp.user_id = user_id
    rp.dependent_id = dependent_id
    rp.status = status
    rp.joined_at = None
    rp.schedules = []
    rp.route = route
    return rp


def test_list_my_routes_empty_returns_empty_list() -> None:
    service, rp_repo, *_ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = []

    result = service.list_my_routes(uuid.uuid4())

    assert result == []


def test_list_my_routes_calls_repo_with_user_id() -> None:
    user_id = uuid.uuid4()
    service, rp_repo, *_ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = []

    service.list_my_routes(user_id)

    rp_repo.find_active_with_route_by_user.assert_called_once_with(user_id)


def test_list_my_routes_returns_one_item_per_membership() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock("Motorista")

    rp_a = make_rp_with_route_mock(uuid.uuid4(), user_id, driver.id, status="accepted")
    rp_b = make_rp_with_route_mock(uuid.uuid4(), user_id, driver.id, status="pending")

    service, rp_repo, _, user_repo, _, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp_a, rp_b]
    user_repo.find_by_id.return_value = driver

    result = service.list_my_routes(user_id)

    assert len(result) == 2


def test_list_my_routes_resolves_driver_name() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock("Carlos Motorista")
    rp = make_rp_with_route_mock(uuid.uuid4(), user_id, driver.id, status="accepted")

    service, rp_repo, _, user_repo, _, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp]
    user_repo.find_by_id.return_value = driver

    result = service.list_my_routes(user_id)

    assert result[0].driver_name == "Carlos Motorista"


def test_list_my_routes_resolves_driver_phone() -> None:
    """US13 — service precisa carregar driver.phone pro deeplink do FE."""
    user_id = uuid.uuid4()
    driver = make_user_mock("Motorista", phone="54988887777")
    rp = make_rp_with_route_mock(uuid.uuid4(), user_id, driver.id, status="accepted")

    service, rp_repo, _, user_repo, _, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp]
    user_repo.find_by_id.return_value = driver

    result = service.list_my_routes(user_id)

    assert result[0].driver_phone == "54988887777"


def test_list_my_routes_exposes_membership_status() -> None:
    """Distingue rp.status (membership) do route.status (rota)."""
    user_id = uuid.uuid4()
    driver = make_user_mock()
    rp = make_rp_with_route_mock(
        uuid.uuid4(), user_id, driver.id,
        status="pending", route_status="ativa",
    )

    service, rp_repo, _, user_repo, _, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp]
    user_repo.find_by_id.return_value = driver

    result = service.list_my_routes(user_id)

    assert result[0].membership_status == "pending"
    assert result[0].status == "ativa"


def test_list_my_routes_resolves_dependent_name_when_present() -> None:
    guardian_id = uuid.uuid4()
    dep = make_dependent_mock("Maria Dependente", guardian_id=guardian_id)
    driver = make_user_mock("Motorista")
    rp = make_rp_with_route_mock(
        uuid.uuid4(), guardian_id, driver.id,
        status="accepted", dependent_id=dep.id,
    )

    service, rp_repo, _, user_repo, dep_repo, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp]
    user_repo.find_by_id.return_value = driver
    dep_repo.find_by_id.return_value = dep

    result = service.list_my_routes(guardian_id)

    assert result[0].dependent_name == "Maria Dependente"


def test_list_my_routes_dependent_name_none_for_self_membership() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock()
    rp = make_rp_with_route_mock(uuid.uuid4(), user_id, driver.id, status="accepted")

    service, rp_repo, _, user_repo, _, _, _, _ = build_service()
    rp_repo.find_active_with_route_by_user.return_value = [rp]
    user_repo.find_by_id.return_value = driver

    result = service.list_my_routes(user_id)

    assert result[0].dependent_name is None


# ===========================================================================
# US14 — RoutePassangerService.get_my_route_detail
# Arquivo: src/domains/route_passangers/service.py
#
# Regras:
#   - 404 RouteNotFoundError se a rota não existir.
#   - 403 NotRoutePassangerError se o par (user_id, dependent_id) não tiver
#     vínculo ativo (pending ou accepted) na rota.
#   - Resolve driver_name/driver_phone via user_repository.
#   - Resolve dependent_name via dependent_repository quando dependent_id != None.
#   - stops ordenados por order_index (via relacionamento da rota).
#   - current_trip_id: None quando route.status != 'em_andamento';
#     caso contrário, o trip.id com status='iniciada' na rota.
#   - Nunca expõe invite_code, max_passengers nem driver_id.
# ===========================================================================


def make_full_route_mock(
    driver_id: uuid.UUID,
    route_name: str = "PUCRS",
    status: str = "ativa",
    recurrence: str = "seg,qua,sex",
    include_trip: bool = False,
):
    """RouteModel com relacionamentos (origin/destination/stops/trips) preenchidos."""
    from datetime import time as dtime

    from src.domains.addresses.entity import AddressModel
    from src.domains.routes.entity import RouteModel
    from src.domains.stops.entity import StopModel
    from src.domains.trips.entity import TripModel

    origin = Mock(spec=AddressModel)
    origin.id = uuid.uuid4()
    origin.label = "Casa"
    origin.street = "Rua X"
    origin.number = "100"
    origin.neighborhood = "Centro"
    origin.zip = "90000-000"
    origin.city = "Porto Alegre"
    origin.state = "RS"
    origin.latitude = None
    origin.longitude = None

    destination = Mock(spec=AddressModel)
    destination.id = uuid.uuid4()
    destination.label = "PUCRS"
    destination.street = "Av. Ipiranga"
    destination.number = "6681"
    destination.neighborhood = "Partenon"
    destination.zip = "90619-900"
    destination.city = "Porto Alegre"
    destination.state = "RS"
    destination.latitude = None
    destination.longitude = None

    stop_a = Mock(spec=StopModel)
    stop_a.id = uuid.uuid4()
    stop_a.order_index = 1
    stop_b = Mock(spec=StopModel)
    stop_b.id = uuid.uuid4()
    stop_b.order_index = 2

    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.name = route_name
    route.route_type = "outbound"
    route.status = status
    route.recurrence = recurrence
    route.expected_time = dtime(7, 30)
    route.driver_id = driver_id
    route.origin_address = origin
    route.destination_address = destination
    route.origin_address_id = origin.id
    route.destination_address_id = destination.id
    route.stops = [stop_a, stop_b]

    if include_trip:
        trip = Mock(spec=TripModel)
        trip.id = uuid.uuid4()
        trip.status = "iniciada"
        route.trips = [trip]
    else:
        route.trips = []

    return route


def make_rp_with_pickup_mock(
    route_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str = "accepted",
    dependent_id=None,
):
    """RP com pickup_address e schedules resolvidos via ORM."""
    from src.domains.addresses.entity import AddressModel
    from src.domains.route_passangers.entity import RoutePassangerModel

    pickup = Mock(spec=AddressModel)
    pickup.id = uuid.uuid4()
    pickup.label = "Embarque"
    pickup.street = "Rua Z"
    pickup.number = "200"
    pickup.neighborhood = "Centro"
    pickup.zip = "90000-001"
    pickup.city = "Porto Alegre"
    pickup.state = "RS"
    pickup.latitude = None
    pickup.longitude = None

    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id
    rp.user_id = user_id
    rp.dependent_id = dependent_id
    rp.status = status
    rp.pickup_address_id = pickup.id
    rp.pickup_address = pickup
    rp.schedules = []
    return rp


def test_get_my_route_detail_success_self_membership_returns_response() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock("Carlos Motorista", phone="51988887777")
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    result = service.get_my_route_detail(route.id, user_id)

    assert result.route_id == route.id
    assert result.name == "PUCRS"
    assert result.driver_name == "Carlos Motorista"
    assert result.driver_phone == "51988887777"
    assert result.membership_status == "accepted"
    assert result.dependent_id is None
    assert result.dependent_name is None
    assert result.current_trip_id is None


def test_get_my_route_detail_route_not_found_raises() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    service, _, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.get_my_route_detail(uuid.uuid4(), uuid.uuid4())


def test_get_my_route_detail_no_active_membership_raises() -> None:
    from src.domains.route_passangers.errors import NotRoutePassangerError

    driver = make_user_mock()
    route = make_full_route_mock(driver.id)

    service, rp_repo, route_repo, _, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = None

    with pytest.raises(NotRoutePassangerError):
        service.get_my_route_detail(route.id, uuid.uuid4())


def test_get_my_route_detail_looks_up_membership_with_correct_args() -> None:
    user_id = uuid.uuid4()
    dependent_id = uuid.uuid4()
    driver = make_user_mock()
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id, dependent_id=dependent_id)

    service, rp_repo, route_repo, user_repo, dep_repo, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver
    dep_repo.find_by_id.return_value = make_dependent_mock("Filha", guardian_id=user_id)

    service.get_my_route_detail(route.id, user_id, dependent_id=dependent_id)

    rp_repo.find_active_by_user_and_route.assert_called_once_with(
        user_id, dependent_id, route.id
    )


def test_get_my_route_detail_resolves_dependent_name_when_dependent_id_present() -> None:
    user_id = uuid.uuid4()
    dependent_id = uuid.uuid4()
    driver = make_user_mock()
    dep = make_dependent_mock("Valentina Fonseca", guardian_id=user_id)
    dep.id = dependent_id
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id, dependent_id=dependent_id)

    service, rp_repo, route_repo, user_repo, dep_repo, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver
    dep_repo.find_by_id.return_value = dep

    result = service.get_my_route_detail(route.id, user_id, dependent_id=dependent_id)

    assert result.dependent_id == dependent_id
    assert result.dependent_name == "Valentina Fonseca"


def test_get_my_route_detail_dependent_name_none_for_self_membership() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock()
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id, dependent_id=None)

    service, rp_repo, route_repo, user_repo, dep_repo, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    result = service.get_my_route_detail(route.id, user_id)

    assert result.dependent_name is None
    dep_repo.find_by_id.assert_not_called()


def test_get_my_route_detail_current_trip_id_set_when_in_progress() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock()
    route = make_full_route_mock(driver.id, status="em_andamento", include_trip=True)
    rp = make_rp_with_pickup_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    result = service.get_my_route_detail(route.id, user_id)

    assert result.status == "em_andamento"
    assert result.current_trip_id == route.trips[0].id


def test_get_my_route_detail_current_trip_id_none_when_route_not_in_progress() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock()
    route = make_full_route_mock(driver.id, status="ativa")
    rp = make_rp_with_pickup_mock(route.id, user_id, status="accepted")

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    result = service.get_my_route_detail(route.id, user_id)

    assert result.current_trip_id is None


def test_get_my_route_detail_resolves_driver_from_route_driver_id() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock("Paula Driver")
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id)

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    service.get_my_route_detail(route.id, user_id)

    user_repo.find_by_id.assert_called_with(driver.id)


def test_get_my_route_detail_my_pickup_address_comes_from_rp() -> None:
    user_id = uuid.uuid4()
    driver = make_user_mock()
    route = make_full_route_mock(driver.id)
    rp = make_rp_with_pickup_mock(route.id, user_id)

    service, rp_repo, route_repo, user_repo, _, _, _, _ = build_service()
    route_repo.find_by_id.return_value = route
    rp_repo.find_active_by_user_and_route.return_value = rp
    user_repo.find_by_id.return_value = driver

    result = service.get_my_route_detail(route.id, user_id)

    assert result.my_pickup_address.id == rp.pickup_address.id
