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
        "user_phone": "51999999999",
        "pickup_address_id": uuid.uuid4(),
        "dependent_id": uuid.uuid4() if dependent else None,
        "dependent_name": "Maria Silva" if dependent else None,
        "guardian_name": "João Silva" if dependent else None,
    }
    return RoutePassangerResponse(**payload)


# ===========================================================================
# TK09 — POST /routes/{route_id}/passangers/{rp_id}/accept
# ===========================================================================


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


def test_reject_request_rp_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_reject_request_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.reject_request.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}/reject", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


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


def test_remove_passanger_success_returns_204() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.remove_passanger.return_value = None
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/{uuid.uuid4()}", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 204


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


def test_list_passangers_invalid_status_returns_422() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_by_status.side_effect = ValueError("status inválido")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(
        f"/routes/{uuid.uuid4()}/passangers?status=foobar", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code in (400, 422)


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
    pickup = AddressModel(
        user_id=user_id,
        label="Casa Passageiro",
        street="Rua Exemplo",
        number="100",
        neighborhood="Centro",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add(pickup)
    db_session.flush()
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=user_id,
        status=status,
        pickup_address_id=pickup.id,
    )
    db_session.add(rp)
    db_session.flush()
    return rp


# ---------------------------------------------------------------------------
# TK09 — integração POST accept
# ---------------------------------------------------------------------------


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


def test_integration_accept_request_persists_stop_in_db(integration_client, db_session) -> None:
    """Após accept bem-sucedido, deve existir uma Stop vinculada ao rp no DB."""
    from src.domains.stops.entity import StopModel

    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 200
    stop = db_session.query(StopModel).filter_by(route_passanger_id=rp.id).first()
    assert stop is not None
    assert stop.route_id == route.id
    assert stop.address_id == rp.pickup_address_id


def test_integration_accept_request_stop_type_matches_outbound(
    integration_client, db_session
) -> None:
    """Rota outbound → stop.type = 'embarque'."""
    from src.domains.stops.entity import StopModel

    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)  # route_type default = 'outbound'
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/accept", headers=headers
    )

    assert response.status_code == 200
    stop = db_session.query(StopModel).filter_by(route_passanger_id=rp.id).first()
    assert stop.type == "embarque"


# ---------------------------------------------------------------------------
# TK11 — integração POST reject
# ---------------------------------------------------------------------------


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


def test_integration_reject_request_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    other_driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id)
    headers = {"X-User-Id": str(other_driver.id), "X-User-Role": "driver"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers/{rp.id}/reject", headers=headers
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK13 — integração DELETE passanger
# ---------------------------------------------------------------------------


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


def test_integration_remove_passanger_deletes_stop_from_db(
    integration_client, db_session
) -> None:
    """Após remove bem-sucedido, a Stop vinculada ao rp não deve mais existir."""
    from src.domains.stops.entity import StopModel

    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    rp_id = rp.id
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    # Cria Stop manualmente para simular que o accept_request já criou uma
    stop = StopModel(
        route_id=route.id,
        route_passanger_id=rp_id,
        address_id=rp.pickup_address_id,
        order_index=0,
        type="embarque",
    )
    db_session.add(stop)
    db_session.flush()
    assert db_session.query(StopModel).filter_by(route_passanger_id=rp_id).first() is not None

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/{rp_id}", headers=headers
    )

    assert response.status_code == 204
    assert db_session.query(StopModel).filter_by(route_passanger_id=rp_id).first() is None


# ---------------------------------------------------------------------------
# TK15 — integração GET passangers
# ---------------------------------------------------------------------------


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


def test_integration_list_passangers_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    other_driver, _ = make_integration_driver(db_session)
    route = make_integration_route(db_session, driver.id)
    headers = {"X-User-Id": str(other_driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{route.id}/passangers", headers=headers
    )

    assert response.status_code == 403


def test_integration_list_passangers_route_not_found_returns_404(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(
        f"/routes/{uuid.uuid4()}/passangers", headers=headers
    )

    assert response.status_code == 404


# ===========================================================================
# US08 — Controller de route_passangers (join/leave/update_schedules)
#
# TK08: POST   /routes/{route_id}/passangers
# TK10: DELETE /routes/{route_id}/passangers/me
# TK12: PATCH  /routes/{route_id}/passangers/me
# ===========================================================================


PASSENGER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "guardian"}


_DEFAULT_ADDRESS_PAYLOAD = {
    "label": "Casa",
    "street": "Rua Teste",
    "number": "123",
    "neighborhood": "Centro",
    "zip": "90000-000",
    "city": "Porto Alegre",
    "state": "RS",
}


def make_join_payload(dependent_id=None, days=("monday",)):
    schedules = [{"day_of_week": d} for d in days]
    payload: dict = {"schedules": schedules, "address": _DEFAULT_ADDRESS_PAYLOAD}
    if dependent_id is not None:
        payload["dependent_id"] = str(dependent_id)
    return payload


# ---------------------------------------------------------------------------
# TK08 — POST /routes/{route_id}/passangers (unidade)
# ---------------------------------------------------------------------------


def test_join_route_success_returns_201() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.join_route.return_value = make_rp_response(status="pending")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json=make_join_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_join_route_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.join_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json=make_join_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_join_route_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.join_route.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json=make_join_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_join_route_full_returns_409() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.join_route.side_effect = RouteCapacityExceededError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json=make_join_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_join_route_duplicate_returns_409() -> None:
    from src.domains.route_passangers.errors import DuplicateRoutePassangerError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.join_route.side_effect = DuplicateRoutePassangerError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json=make_join_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_join_route_invalid_payload_returns_422() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/passangers",
        json={"schedules": []},  # lista vazia — inválido
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TK08 — POST /routes/{route_id}/passangers (integração)
# ---------------------------------------------------------------------------


def test_integration_join_route_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session, "Integ Ana")
    route = make_integration_route(db_session, driver.id)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers",
        json=make_join_payload(days=("monday",)),
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_integration_join_route_creates_schedules(integration_client, db_session) -> None:
    from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel

    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers",
        json=make_join_payload(days=("monday", "wednesday")),
        headers=headers,
    )

    assert response.status_code == 201
    rp_id = uuid.UUID(response.json()["id"])
    schedules = (
        db_session.query(RoutePassangerScheduleModel)
        .filter(RoutePassangerScheduleModel.route_passanger_id == rp_id)
        .all()
    )
    assert len(schedules) == 2


def test_integration_join_route_duplicate_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="pending")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers",
        json=make_join_payload(),
        headers=headers,
    )

    assert response.status_code == 409


def test_integration_join_route_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.post(
        f"/routes/{route.id}/passangers",
        json=make_join_payload(),
        headers=headers,
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# TK10 — DELETE /routes/{route_id}/passangers/me (unidade)
# ---------------------------------------------------------------------------


def test_leave_route_success_returns_204() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.leave_route.return_value = None
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/me",
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 204


def test_leave_route_with_dependent_id_query_forwarded() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.leave_route.return_value = None
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service
    dep_id = uuid.uuid4()

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/me?dependent_id={dep_id}",
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 204
    call_kwargs = mock_service.leave_route.call_args.kwargs
    call_args = mock_service.leave_route.call_args.args
    assert dep_id in call_args or call_kwargs.get("dependent_id") == dep_id


def test_leave_route_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.leave_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/me",
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_leave_route_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.leave_route.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/me",
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_leave_route_rp_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.leave_route.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.delete(
        f"/routes/{uuid.uuid4()}/passangers/me",
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# TK10 — DELETE /routes/{route_id}/passangers/me (integração)
# ---------------------------------------------------------------------------


def test_integration_leave_route_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="pending")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/me", headers=headers
    )

    assert response.status_code == 204


def test_integration_leave_route_no_active_rp_returns_404(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/me", headers=headers
    )

    assert response.status_code == 404


def test_integration_leave_route_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.delete(
        f"/routes/{route.id}/passangers/me", headers=headers
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# TK12 — PATCH /routes/{route_id}/passangers/me (unidade)
# ---------------------------------------------------------------------------


def make_update_payload(days=("monday",), address_id=None):
    address_id = address_id or str(uuid.uuid4())
    return {
        "schedules": [
            {"day_of_week": d, "address_id": address_id} for d in days
        ]
    }


def test_update_schedules_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.update_schedules.return_value = make_rp_response(status="pending")
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me",
        json=make_update_payload(days=("monday", "friday")),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200


def test_update_schedules_with_dependent_id_query_forwarded() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.update_schedules.return_value = make_rp_response(status="pending", dependent=True)
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service
    dep_id = uuid.uuid4()

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me?dependent_id={dep_id}",
        json=make_update_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    call_kwargs = mock_service.update_schedules.call_args.kwargs
    call_args = mock_service.update_schedules.call_args.args
    assert dep_id in call_args or call_kwargs.get("dependent_id") == dep_id


def test_update_schedules_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.update_schedules.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me",
        json=make_update_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_update_schedules_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.update_schedules.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me",
        json=make_update_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_update_schedules_rp_not_found_returns_404() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.update_schedules.side_effect = RoutePassangerNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me",
        json=make_update_payload(),
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_update_schedules_invalid_payload_returns_422() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.patch(
        f"/routes/{uuid.uuid4()}/passangers/me",
        json={"schedules": []},
        headers=PASSENGER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TK12 — PATCH /routes/{route_id}/passangers/me (integração)
# ---------------------------------------------------------------------------


def make_integration_pickup_address(db_session, user_id):
    """Cria um endereço de embarque diretamente na DB para testes de update_schedules.

    Necessário nesse contexto porque UpdateSchedulesRequest ainda recebe address_id
    explícito (ao contrário de JoinRouteRequest que cria o endereço inline).
    """
    addr = AddressModel(
        user_id=user_id,
        label="Casa",
        street="Rua Teste",
        number="123",
        neighborhood="Centro",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add(addr)
    db_session.flush()
    return addr


def test_integration_update_schedules_success(integration_client, db_session) -> None:
    from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel

    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    address = make_integration_pickup_address(db_session, passenger.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.patch(
        f"/routes/{route.id}/passangers/me",
        json=make_update_payload(days=("monday", "thursday"), address_id=str(address.id)),
        headers=headers,
    )

    assert response.status_code == 200
    schedules = (
        db_session.query(RoutePassangerScheduleModel)
        .filter(RoutePassangerScheduleModel.route_passanger_id == rp.id)
        .all()
    )
    assert len(schedules) == 2


def test_integration_update_schedules_no_active_rp_returns_404(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    address = make_integration_pickup_address(db_session, passenger.id)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.patch(
        f"/routes/{route.id}/passangers/me",
        json=make_update_payload(address_id=str(address.id)),
        headers=headers,
    )

    assert response.status_code == 404


def test_integration_update_schedules_in_progress_returns_409(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, status="em_andamento")
    address = make_integration_pickup_address(db_session, passenger.id)
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.patch(
        f"/routes/{route.id}/passangers/me",
        json=make_update_payload(address_id=str(address.id)),
        headers=headers,
    )

    assert response.status_code == 409


# ===========================================================================
# US08-TK15 — GET /routes/me (home do passageiro)
# ===========================================================================


def make_passanger_route_response(
    membership_status: str = "accepted",
    dependent_name: str | None = None,
    route_name: str = "PUCRS",
    driver_phone: str = "51999999999",
):
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = {
        "route_id": uuid.uuid4(),
        "route_name": route_name,
        "driver_name": "Carlos Motorista",
        "driver_phone": driver_phone,
        "origin_label": "Casa",
        "destination_label": "PUCRS",
        "expected_time": time(8, 0),
        "recurrence": ["seg", "ter", "qua", "qui", "sex"],
        "status": "ativa",
        "membership_status": membership_status,
        "schedules": [],
        "joined_at": datetime(2026, 4, 18, 10, 0, 0),
        "dependent_name": dependent_name,
    }
    return PassangerRouteResponse(**payload)


def test_list_my_routes_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_my_routes.return_value = [
        make_passanger_route_response(membership_status="accepted"),
        make_passanger_route_response(membership_status="pending", route_name="Trabalho"),
    ]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    headers = {"X-User-Id": str(uuid.uuid4())}
    response = client.get("/routes/me", headers=headers)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_list_my_routes_empty_returns_200_with_empty_list() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_my_routes.return_value = []
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    headers = {"X-User-Id": str(uuid.uuid4())}
    response = client.get("/routes/me", headers=headers)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


def test_list_my_routes_calls_service_with_user_id() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_my_routes.return_value = []
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    user_id = uuid.uuid4()
    headers = {"X-User-Id": str(user_id)}
    client.get("/routes/me", headers=headers)

    app.dependency_overrides.clear()
    assert mock_service.list_my_routes.call_args.args[0] == user_id


def test_list_my_routes_exposes_dependent_name_when_present() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_my_routes.return_value = [
        make_passanger_route_response(dependent_name="Maria Silva"),
    ]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    headers = {"X-User-Id": str(uuid.uuid4())}
    response = client.get("/routes/me", headers=headers)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["dependent_name"] == "Maria Silva"


def test_list_my_routes_exposes_driver_phone() -> None:
    """US13 — driver_phone precisa chegar no response pro FE montar deeplink."""
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.list_my_routes.return_value = [
        make_passanger_route_response(driver_phone="54988887777"),
    ]
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    headers = {"X-User-Id": str(uuid.uuid4())}
    response = client.get("/routes/me", headers=headers)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["driver_phone"] == "54988887777"


# ---------------------------------------------------------------------------
# Integração — GET /routes/me
# ---------------------------------------------------------------------------


def test_integration_list_my_routes_returns_active_memberships(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route_a = make_integration_route(db_session, driver.id)
    route_b = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route_a.id, passenger.id, status="accepted")
    make_integration_rp(db_session, route_b.id, passenger.id, status="pending")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get("/routes/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_integration_list_my_routes_empty_returns_empty_list(integration_client, db_session) -> None:
    passenger = make_integration_passenger(db_session)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.get("/routes/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_integration_list_my_routes_ignores_rejected_and_removed(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route_a = make_integration_route(db_session, driver.id)
    route_b = make_integration_route(db_session, driver.id)
    route_c = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route_a.id, passenger.id, status="rejected")
    make_integration_rp(db_session, route_b.id, passenger.id, status="removed")
    make_integration_rp(db_session, route_c.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get("/routes/me", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_integration_list_my_routes_does_not_collide_with_route_by_id(integration_client, db_session) -> None:
    """GET /routes/me deve ser resolvido como rota literal, não cair no
    matcher de GET /routes/{route_id} (que rejeitaria 'me' como UUID)."""
    passenger = make_integration_passenger(db_session)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.get("/routes/me", headers=headers)

    # Não pode ser 422 (UUID parse fail do path /routes/{route_id})
    assert response.status_code != 422
    assert response.status_code == 200


# ===========================================================================
# US14 — GET /routes/{route_id}/me (UNIDADE)
# ===========================================================================


PASSENGER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "guardian"}


def make_detail_response(
    *, status: str = "ativa", membership_status: str = "accepted",
    dependent_id=None, dependent_name=None, current_trip_id=None,
):
    from datetime import time as dtime

    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse
    from src.domains.routes.dtos import AddressResponse

    def _addr(label: str) -> AddressResponse:
        return AddressResponse(
            id=uuid.uuid4(),
            label=label,
            street="Rua Z",
            number="100",
            neighborhood="Centro",
            zip="90000-000",
            city="Porto Alegre",
            state="RS",
        )

    return PassangerRouteDetailResponse(
        route_id=uuid.uuid4(),
        name="PUCRS",
        route_type="outbound",
        status=status,
        recurrence=["seg", "qua", "sex"],
        expected_time=dtime(7, 30),
        origin_address=_addr("Casa"),
        destination_address=_addr("PUCRS"),
        stops=[],
        driver_name="Carlos Motorista",
        driver_phone="51988887777",
        membership_status=membership_status,
        dependent_id=dependent_id,
        dependent_name=dependent_name,
        my_pickup_address=_addr("Embarque"),
        my_schedules=[],
        current_trip_id=current_trip_id,
    )


def test_get_my_route_detail_success_returns_200() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.return_value = make_detail_response()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/me", headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "PUCRS"
    assert body["membership_status"] == "accepted"
    assert body["driver_phone"] == "51988887777"


def test_get_my_route_detail_does_not_expose_driver_id_or_invite_code() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.return_value = make_detail_response()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/me", headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    body = response.json()
    assert "invite_code" not in body
    assert "max_passengers" not in body
    assert "driver_id" not in body


def test_get_my_route_detail_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/me", headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_get_my_route_detail_not_passanger_returns_403() -> None:
    from src.domains.route_passangers.errors import NotRoutePassangerError

    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.side_effect = NotRoutePassangerError()
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/me", headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_get_my_route_detail_forwards_dependent_id_query_param() -> None:
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.return_value = make_detail_response(
        dependent_id=uuid.uuid4(), dependent_name="Valentina"
    )
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    route_id = uuid.uuid4()
    dep_id = uuid.uuid4()
    response = client.get(
        f"/routes/{route_id}/me?dependent_id={dep_id}", headers=PASSENGER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    call_args = mock_service.get_my_route_detail.call_args
    assert call_args.kwargs.get("dependent_id") == dep_id or dep_id in call_args.args


def test_get_my_route_detail_current_trip_id_when_in_progress() -> None:
    trip_id = uuid.uuid4()
    mock_service = Mock(spec=RoutePassangerService)
    mock_service.get_my_route_detail.return_value = make_detail_response(
        status="em_andamento", current_trip_id=trip_id
    )
    app.dependency_overrides[get_route_passanger_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}/me", headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["current_trip_id"] == str(trip_id)


# ===========================================================================
# US14 — GET /routes/{route_id}/me (INTEGRAÇÃO)
# ===========================================================================


@pytest.mark.skip(reason="US06-TK06, US08-TK03)")
def test_integration_get_my_route_detail_success(integration_client, db_session) -> None:
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session, "Integ Mateus")
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get(f"/routes/{route.id}/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "PUCRS"
    assert body["membership_status"] == "accepted"
    assert body["driver_name"] == "Motorista Int"
    # Não expõe campos do motorista
    assert "invite_code" not in body
    assert "driver_id" not in body


@pytest.mark.skip(reason="US06-TK06, US08-TK03")
def test_integration_get_my_route_detail_route_not_found_returns_404(
    integration_client, db_session
) -> None:
    passenger = make_integration_passenger(db_session)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.get(f"/routes/{uuid.uuid4()}/me", headers=headers)

    assert response.status_code == 404


@pytest.mark.skip(reason="US06-TK06, US08-TK03")
def test_integration_get_my_route_detail_not_passanger_returns_403(
    integration_client, db_session
) -> None:
    driver, _ = make_integration_driver(db_session)
    outsider = make_integration_passenger(db_session, "Outsider")
    route = make_integration_route(db_session, driver.id)

    headers = {"X-User-Id": str(outsider.id), "X-User-Role": "guardian"}
    response = integration_client.get(f"/routes/{route.id}/me", headers=headers)

    assert response.status_code == 403


@pytest.mark.skip(reason="US06-TK06, US08-TK03")
def test_integration_get_my_route_detail_pending_membership_allowed(
    integration_client, db_session
) -> None:
    """Passageiro ainda com status pending deve conseguir ver os detalhes."""
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="pending")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get(f"/routes/{route.id}/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["membership_status"] == "pending"


@pytest.mark.skip(reason="US06-TK06, US08-TK03")
def test_integration_get_my_route_detail_does_not_collide_with_route_by_id(
    integration_client, db_session
) -> None:
    """GET /routes/{uuid}/me deve ser resolvido pelo route_passanger controller
    (que é registrado antes) e não pela rota genérica GET /routes/{route_id}."""
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get(f"/routes/{route.id}/me", headers=headers)

    # Se caísse em GET /routes/{route_id} o passageiro levaria 403
    # (RouteOwnershipError — driver-only) em vez de 200.
    assert response.status_code == 200


@pytest.mark.skip(reason="US06-TK06, US08-TK03")
def test_integration_get_my_route_detail_rejected_membership_returns_403(
    integration_client, db_session
) -> None:
    """Vínculo com status='rejected' não é ativo — deve retornar 403."""
    driver, _ = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="rejected")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.get(f"/routes/{route.id}/me", headers=headers)

    assert response.status_code == 403
