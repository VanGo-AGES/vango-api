import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.domains.route_passangers.service import RoutePassangerService
from src.infrastructure.dependencies.route_passanger_dependencies import (
    get_route_passanger_service,
)
from src.main import app

client = TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# US06 — Controller de route_passangers (testes de unidade com mocks)
#
# TK09: POST   /routes/{route_id}/passangers/{rp_id}/accept
# TK11: POST   /routes/{route_id}/passangers/{rp_id}/reject
# TK13: DELETE /routes/{route_id}/passangers/{rp_id}
# TK15: GET    /routes/{route_id}/passangers?status=...
# ===========================================================================


DRIVER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "driver"}


def make_rp_response(status: str = "accepted", dependent: bool = False):
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = {
        "id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "status": status,
        "requested_at": datetime(2026, 4, 18, 10, 0, 0),
        "joined_at": datetime(2026, 4, 18, 11, 0, 0) if status == "accepted" else None,
        "user_id": uuid.uuid4(),
        "user_name": "João Silva",
        "dependent_id": uuid.uuid4() if dependent else None,
        "dependent_name": "Maria Silva" if dependent else None,
        "guardian_name": "João Silva" if dependent else None,
    }
    return RoutePassangerResponse(**payload)


# ===========================================================================
# TK09 — POST /routes/{route_id}/passangers/{rp_id}/accept
# ===========================================================================


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.return_value = make_rp_response(status="accepted")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_rp_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_already_processed_returns_409() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RoutePassangerAlreadyProcessedError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK09")
def test_accept_request_capacity_exceeded_returns_409() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.accept_request.side_effect = RouteCapacityExceededError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/accept", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK11 — POST /routes/{route_id}/passangers/{rp_id}/reject
# ===========================================================================


@pytest.mark.skip(reason="US06-TK11")
def test_reject_request_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.return_value = make_rp_response(status="rejected")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.skip(reason="US06-TK11")
def test_reject_request_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK11")
def test_reject_request_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK11")
def test_reject_request_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK11")
def test_reject_request_already_processed_returns_409() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RoutePassangerAlreadyProcessedError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK13 — DELETE /routes/{route_id}/passangers/{rp_id}
# ===========================================================================


@pytest.mark.skip(reason="US06-TK13")
def test_remove_passanger_success_returns_204() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.return_value = None
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 204


@pytest.mark.skip(reason="US06-TK13")
def test_remove_passanger_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK13")
def test_remove_passanger_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK13")
def test_remove_passanger_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK13")
def test_remove_passanger_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK15 — GET /routes/{route_id}/passangers?status=
# ===========================================================================


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.return_value = [
        make_rp_response(status="pending"),
        make_rp_response(status="pending"),
    ]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=pending", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_filters_by_status() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.return_value = []
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    route_id = uuid.uuid4()
    client.get(f"/routes/{route_id}/passangers?status=accepted", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    called_args = mock_service.list_by_status.call_args
    # status deve ser passado como 'accepted'
    assert "accepted" in called_args.args or called_args.kwargs.get("status") == "accepted"


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_no_filter_returns_all() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.return_value = [
        make_rp_response(status="pending"),
        make_rp_response(status="accepted"),
        make_rp_response(status="rejected"),
    ]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/passangers", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=pending", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=pending", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_invalid_status_returns_422() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.side_effect = ValueError("status inválido")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=foobar", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code in (400, 422)


@pytest.mark.skip(reason="US06-TK15")
def test_list_passangers_response_includes_names() -> None:
    """GET /passangers deve expor user_name, dependent_name e guardian_name."""
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.return_value = [make_rp_response(status="pending", dependent=True)]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=pending", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    body = response.json()[0]
    assert "user_name" in body
    assert "dependent_name" in body
    assert "guardian_name" in body


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db.
# Auth via headers X-User-Id / X-User-Role (sem Firebase).
# ===========================================================================

from datetime import time

from src.domains.addresses.entity import AddressModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.routes.entity import RouteModel
from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel
from src.infrastructure.database import get_db


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def make_integration_driver(db_session):
    driver = UserModel(
        name="Motorista Int",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    vehicle = VehicleModel(
        driver_id=driver.id,
        plate=f"RIT{str(uuid.uuid4())[:4].upper()}",
        capacity=3,
    )
    db_session.add(vehicle)
    db_session.flush()
    return driver, vehicle


def make_integration_passenger(db_session, name: str = "Passageiro"):
    user = UserModel(
        name=name,
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="guardian",
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_integration_route(db_session, driver_id, max_passengers: int = 3, status: str = "ativa"):
    origin = AddressModel(
        user_id=driver_id,
        label="Casa",
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    dest = AddressModel(
        user_id=driver_id,
        label="PUCRS",
        street="Av. Ipiranga",
        number="6681",
        neighborhood="Partenon",
        zip="90619-900",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add_all([origin, dest])
    db_session.flush()

    route = RouteModel(
        driver_id=driver_id,
        origin_address_id=origin.id,
        destination_address_id=dest.id,
        name="PUCRS",
        route_type="outbound",
        recurrence="seg,ter,qua,qui,sex",
        max_passengers=max_passengers,
        expected_time=time(8, 0),
        status=status,
        invite_code=f"IT{str(uuid.uuid4())[:3].upper()}",
    )
    db_session.add(route)
    db_session.flush()
    return route


def make_integration_rp(db_session, route_id, user_id, status: str = "pending"):
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=user_id,
        status=status,
    )
    db_session.add(rp)
    db_session.flush()
    return rp


# ---------------------------------------------------------------------------
# TK09 — integração POST accept
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK09")
def test_integration_accept_request_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session, "Integ João")
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.skip(reason="US06-TK09")
def test_integration_accept_request_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK09")
def test_integration_accept_request_capacity_exceeded_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id, max_passengers=1)
    already_in = make_integration_passenger(db_session, "Já aceito")
    make_integration_rp(db_session, route.id, already_in.id, status="accepted")

    new_passenger = make_integration_passenger(db_session, "Novo")
    rp = make_integration_rp(db_session, route.id, new_passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK09")
def test_integration_accept_request_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    other_driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(other_driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK11 — integração POST reject
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK11")
def test_integration_reject_request_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/reject", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.skip(reason="US06-TK11")
def test_integration_reject_request_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/reject", headers=headers
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK11")
def test_integration_reject_request_already_processed_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/reject", headers=headers
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# TK13 — integração DELETE passanger
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK13")
def test_integration_remove_passanger_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/{rp.id}", headers=headers
    )

    assert response.status_code == 204


@pytest.mark.skip(reason="US06-TK13")
def test_integration_remove_passanger_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/{rp.id}", headers=headers
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US06-TK13")
def test_integration_remove_passanger_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    other_driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(other_driver.id), "X-User-Role": "driver"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/{rp.id}", headers=headers
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK15 — integração GET passangers
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK15")
def test_integration_list_passangers_filter_pending(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id)
    p1 = make_integration_passenger(db_session, "P1")
    p2 = make_integration_passenger(db_session, "P2")
    p3 = make_integration_passenger(db_session, "P3")
    make_integration_rp(db_session, route.id, p1.id, status="pending")
    make_integration_rp(db_session, route.id, p2.id, status="pending")
    make_integration_rp(db_session, route.id, p3.id, status="accepted")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{route.id}/passangers?status=pending", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(rp["status"] == "pending" for rp in data)


@pytest.mark.skip(reason="US06-TK15")
def test_integration_list_passangers_no_filter_returns_all(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id)
    p1 = make_integration_passenger(db_session, "P1")
    p2 = make_integration_passenger(db_session, "P2")
    make_integration_rp(db_session, route.id, p1.id, status="pending")
    make_integration_rp(db_session, route.id, p2.id, status="accepted")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{route.id}/passangers", headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.skip(reason="US06-TK15")
def test_integration_list_passangers_resolves_user_name(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id)
    passenger = make_integration_passenger(db_session, "Maria da Silva")
    make_integration_rp(db_session, route.id, passenger.id, status="pending")
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{route.id}/passangers?status=pending", headers=headers
    )

    assert response.status_code == 200
    assert response.json()[0]["user_name"] == "Maria da Silva"


@pytest.mark.skip(reason="US06-TK15")
def test_integration_list_passangers_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    other_driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id)
    headers = {"X-User-Id": str(other_driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{route.id}/passangers", headers=headers
    )

    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK15")
def test_integration_list_passangers_route_not_found_returns_404(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{uuid.uuid4()}/passangers", headers=headers
    )

    assert response.status_code == 404
