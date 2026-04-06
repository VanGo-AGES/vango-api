import uuid
from datetime import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.domains.routes.service import RouteService
from src.infrastructure.dependencies.route_dependencies import get_route_service
from src.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_route_response_mock(driver_id: uuid.UUID = None):
    from src.domains.routes.dtos import AddressResponse, RouteResponse

    addr = AddressResponse(
        id=uuid.uuid4(),
        label="Casa",
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    return RouteResponse(
        id=uuid.uuid4(),
        name="PUCRS",
        route_type="outbound",
        status="inativa",
        recurrence="seg,ter,qua,qui,sex",
        expected_time=time(8, 0),
        invite_code="A1B2C",
        max_passengers=5,
        origin_address=addr,
        destination_address=addr,
    )


def make_route_payload(**kwargs) -> dict:
    defaults = {
        "name": "PUCRS",
        "route_type": "outbound",
        "origin": {
            "label": "Casa",
            "street": "Av. Coronel Marcos",
            "number": "861",
            "neighborhood": "Três Figueiras",
            "zip": "91760-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "destination": {
            "label": "PUCRS",
            "street": "Av. Ipiranga",
            "number": "6681",
            "neighborhood": "Partenon",
            "zip": "90619-900",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "expected_time": "08:00:00",
        "recurrence": "seg,ter,qua,qui,sex",
    }
    defaults.update(kwargs)
    return defaults


DRIVER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "driver"}


# ===========================================================================
# US05 - TK04: POST /routes/ — criar rota
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


def test_create_route_success_returns_201() -> None:
    """POST /routes/ com payload válido deve retornar 201 e a rota criada."""
    mock_service = Mock(spec=RouteService)
    mock_service.create_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["invite_code"] == "A1B2C"


def test_create_route_missing_name_returns_422() -> None:
    """POST /routes/ sem nome deve retornar 422."""
    payload = make_route_payload()
    del payload["name"]
    response = client.post("/routes/", json=payload, headers=DRIVER_HEADERS)
    assert response.status_code == 422


def test_create_route_invalid_route_type_returns_422() -> None:
    """POST /routes/ com route_type inválido deve retornar 422."""
    response = client.post("/routes/", json=make_route_payload(route_type="ambos"), headers=DRIVER_HEADERS)
    assert response.status_code == 422


def test_create_route_invalid_recurrence_returns_422() -> None:
    """POST /routes/ com dias de recorrência inválidos deve retornar 422."""
    response = client.post("/routes/", json=make_route_payload(recurrence="monday,tuesday"), headers=DRIVER_HEADERS)
    assert response.status_code == 422


def test_create_route_no_vehicle_returns_400() -> None:
    """POST /routes/ quando motorista não tem veículo deve retornar 400."""
    from src.domains.routes.errors import NoVehicleError

    mock_service = Mock(spec=RouteService)
    mock_service.create_route.side_effect = NoVehicleError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_create_route_response_has_correct_fields() -> None:
    """A resposta deve conter todos os campos esperados incluindo endereços aninhados."""
    mock_service = Mock(spec=RouteService)
    mock_service.create_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    body = response.json()
    assert "invite_code" in body
    assert "origin_address" in body
    assert "destination_address" in body
    assert "status" in body
    assert body["status"] == "inativa"


# ===========================================================================
# US05 - TK05: POST /routes/{id}/invite-code/regenerate
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_success_returns_200() -> None:
    """POST /routes/{id}/invite-code/regenerate deve retornar 200 com novo código."""
    route_id = uuid.uuid4()
    updated = make_route_response_mock()
    updated.invite_code = "NEW99"

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.return_value = updated
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{route_id}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["invite_code"] == "NEW99"


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_not_found_returns_404() -> None:
    """POST /routes/{id}/invite-code/regenerate com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_wrong_owner_returns_403() -> None:
    """POST /routes/{id}/invite-code/regenerate por motorista que não é dono deve retornar 403."""
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


# ===========================================================================
# US07 - TK04: GET /routes/ e GET /routes/{id}
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


@pytest.mark.skip(reason="US07-TK04")
def test_list_routes_success_returns_200() -> None:
    """GET /routes/ deve retornar 200 e lista de rotas do motorista."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = [make_route_response_mock(), make_route_response_mock()]
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.skip(reason="US07-TK04")
def test_list_routes_empty_returns_empty_list() -> None:
    """GET /routes/ sem rotas deve retornar 200 com lista vazia."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = []
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_success_returns_200() -> None:
    """GET /routes/{id} deve retornar 200 com dados completos da rota."""
    route_id = uuid.uuid4()
    mock_service = Mock(spec=RouteService)
    mock_service.get_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{route_id}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert "origin_address" in body
    assert "destination_address" in body


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_not_found_returns_404() -> None:
    """GET /routes/{id} com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.get_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_wrong_owner_returns_403() -> None:
    """GET /routes/{id} por motorista que não é dono deve retornar 403."""
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.get_route.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db.
# Auth via headers X-User-Id / X-User-Role (sem Firebase).
# ===========================================================================

from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel
from src.infrastructure.database import get_db
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl
from src.infrastructure.repositories.route_repository import RouteRepositoryImpl


def make_driver_with_vehicle(db_session):
    """Cria um motorista e um veículo associado no banco. Retorna (user, vehicle)."""
    driver = UserModel(
        name="Motorista Integração",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()

    vehicle_repo = VehicleRepositoryImpl(db_session)
    vehicle = vehicle_repo.create(VehicleModel(driver_id=driver.id, plate=f"RIT{str(uuid.uuid4())[:4].upper()}", capacity=5))

    return driver, vehicle


def make_driver_only(db_session) -> UserModel:
    driver = UserModel(
        name="Motorista Sem Veículo",
        email=f"noveh_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    return driver


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def route_payload(**kwargs) -> dict:
    defaults = {
        "name": "PUCRS",
        "route_type": "outbound",
        "origin": {
            "label": "Casa",
            "street": "Av. Coronel Marcos",
            "number": "861",
            "neighborhood": "Três Figueiras",
            "zip": "91760-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "destination": {
            "label": "PUCRS",
            "street": "Av. Ipiranga",
            "number": "6681",
            "neighborhood": "Partenon",
            "zip": "90619-900",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "expected_time": "08:00:00",
        "recurrence": "seg,ter,qua,qui,sex",
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# POST /routes/
# ---------------------------------------------------------------------------


def test_integration_create_route_success(integration_client, db_session) -> None:
    """[Integração] POST /routes/ com motorista e veículo deve retornar 201."""
    driver, vehicle = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post("/routes/", json=route_payload(), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert "invite_code" in body
    assert body["max_passengers"] == vehicle.capacity


def test_integration_create_route_no_vehicle_returns_400(integration_client, db_session) -> None:
    """[Integração] POST /routes/ por motorista sem veículo deve retornar 400."""
    driver = make_driver_only(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post("/routes/", json=route_payload(), headers=headers)

    assert response.status_code == 400


def test_integration_create_route_invalid_recurrence_returns_422(integration_client, db_session) -> None:
    """[Integração] POST /routes/ com recorrência inválida deve retornar 422."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post("/routes/", json=route_payload(recurrence="monday,tuesday"), headers=headers)

    assert response.status_code == 422


def test_integration_create_route_invalid_type_returns_422(integration_client, db_session) -> None:
    """[Integração] POST /routes/ com route_type inválido deve retornar 422."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post("/routes/", json=route_payload(route_type="ambos"), headers=headers)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /routes/{id}/invite-code/regenerate
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US05-TK05")
def test_integration_regenerate_invite_code_success(integration_client, db_session) -> None:
    """[Integração] POST regenerate deve retornar 200 com novo invite_code."""
    driver, vehicle = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]
    original_code = create_response.json()["invite_code"]

    response = integration_client.post(f"/routes/{route_id}/invite-code/regenerate", headers=headers)

    assert response.status_code == 200
    assert response.json()["invite_code"] != original_code


@pytest.mark.skip(reason="US05-TK05")
def test_integration_regenerate_invite_code_not_found_returns_404(integration_client, db_session) -> None:
    """[Integração] POST regenerate com rota inexistente deve retornar 404."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=headers)

    assert response.status_code == 404


@pytest.mark.skip(reason="US05-TK05")
def test_integration_regenerate_invite_code_wrong_owner_returns_403(integration_client, db_session) -> None:
    """[Integração] POST regenerate por motorista que não é dono deve retornar 403."""
    driver1, vehicle1 = make_driver_with_vehicle(db_session)
    driver2, _ = make_driver_with_vehicle(db_session)

    create_response = integration_client.post(
        "/routes/", json=route_payload(),
        headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"},
    )
    route_id = create_response.json()["id"]

    response = integration_client.post(
        f"/routes/{route_id}/invite-code/regenerate",
        headers={"X-User-Id": str(driver2.id), "X-User-Role": "driver"},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /routes/
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US07-TK04")
def test_integration_list_routes_empty(integration_client, db_session) -> None:
    """[Integração] GET /routes/ sem rotas deve retornar 200 com lista vazia."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get("/routes/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.skip(reason="US07-TK04")
def test_integration_list_routes_returns_own_only(integration_client, db_session) -> None:
    """[Integração] GET /routes/ deve retornar apenas rotas do motorista autenticado."""
    driver1, _ = make_driver_with_vehicle(db_session)
    driver2, _ = make_driver_with_vehicle(db_session)

    integration_client.post("/routes/", json=route_payload(name="Rota D1"), headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"})
    integration_client.post("/routes/", json=route_payload(name="Rota D2"), headers={"X-User-Id": str(driver2.id), "X-User-Role": "driver"})

    response = integration_client.get("/routes/", headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Rota D1"


# ---------------------------------------------------------------------------
# GET /routes/{route_id}
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US07-TK04")
def test_integration_get_route_success(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} deve retornar 200 com dados completos da rota."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]

    response = integration_client.get(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert "origin_address" in body
    assert "destination_address" in body
    assert "invite_code" in body


@pytest.mark.skip(reason="US07-TK04")
def test_integration_get_route_not_found_returns_404(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} com id inexistente deve retornar 404."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(f"/routes/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


@pytest.mark.skip(reason="US07-TK04")
def test_integration_get_route_wrong_owner_returns_403(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} por motorista que não é dono deve retornar 403."""
    driver1, _ = make_driver_with_vehicle(db_session)
    driver2, _ = make_driver_with_vehicle(db_session)

    create_response = integration_client.post(
        "/routes/", json=route_payload(),
        headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"},
    )
    route_id = create_response.json()["id"]

    response = integration_client.get(
        f"/routes/{route_id}",
        headers={"X-User-Id": str(driver2.id), "X-User-Role": "driver"},
    )

    assert response.status_code == 403
