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


def test_regenerate_invite_code_not_found_returns_404() -> None:
    """POST /routes/{id}/invite-code/regenerate com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


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


def test_list_routes_success_returns_200() -> None:
    """GET /routes/ deve retornar 200 e lista de rotas do motorista."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = [make_route_response_mock(), make_route_response_mock()]
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_routes_empty_returns_empty_list() -> None:
    """GET /routes/ sem rotas deve retornar 200 com lista vazia."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = []
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


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


def test_get_route_not_found_returns_404() -> None:
    """GET /routes/{id} com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.get_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


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


def test_integration_regenerate_invite_code_not_found_returns_404(integration_client, db_session) -> None:
    """[Integração] POST regenerate com rota inexistente deve retornar 404."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=headers)

    assert response.status_code == 404


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


def test_integration_list_routes_empty(integration_client, db_session) -> None:
    """[Integração] GET /routes/ sem rotas deve retornar 200 com lista vazia."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get("/routes/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


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


def test_integration_get_route_not_found_returns_404(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} com id inexistente deve retornar 404."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get(f"/routes/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


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


# ===========================================================================
# US06 - TK04: PUT /routes/{route_id} — editar rota
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


def test_update_route_success_returns_200() -> None:
    """PUT /routes/{id} com payload válido deve retornar 200 e a rota atualizada."""
    route_id = uuid.uuid4()
    mock_service = Mock(spec=RouteService)
    mock_service.update_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.put(f"/routes/{route_id}", json={"name": "Nova"}, headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200


def test_update_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.update_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.put(f"/routes/{uuid.uuid4()}", json={"name": "Nova"}, headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_update_route_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.update_route.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.put(f"/routes/{uuid.uuid4()}", json={"name": "Nova"}, headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_update_route_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RouteService)
    mock_service.update_route.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.put(f"/routes/{uuid.uuid4()}", json={"name": "Nova"}, headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_update_route_invalid_recurrence_returns_422() -> None:
    response = client.put(
        f"/routes/{uuid.uuid4()}",
        json={"recurrence": "monday,tuesday"},
        headers=DRIVER_HEADERS,
    )
    assert response.status_code == 422


def test_update_route_invalid_route_type_returns_422() -> None:
    response = client.put(
        f"/routes/{uuid.uuid4()}", json={"route_type": "ambos"}, headers=DRIVER_HEADERS
    )
    assert response.status_code == 422


# --- Integração ---


def test_integration_update_route_success_updates_name(integration_client, db_session) -> None:
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]

    response = integration_client.put(f"/routes/{route_id}", json={"name": "Rota Editada"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Rota Editada"


def test_integration_update_route_replaces_origin_address(integration_client, db_session) -> None:
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]
    old_origin_id = create_response.json()["origin_address"]["id"]

    new_origin = {
        "label": "Nova Casa",
        "street": "Rua Nova",
        "number": "100",
        "neighborhood": "Menino Deus",
        "zip": "90000-000",
        "city": "Porto Alegre",
        "state": "RS",
    }
    response = integration_client.put(f"/routes/{route_id}", json={"origin": new_origin}, headers=headers)

    assert response.status_code == 200
    assert response.json()["origin_address"]["id"] != old_origin_id


def test_integration_update_route_in_progress_returns_409(integration_client, db_session) -> None:
    from src.domains.routes.entity import RouteModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]

    # Força status em_andamento direto no banco
    route = db_session.query(RouteModel).filter_by(id=uuid.UUID(route_id)).first()
    route.status = "em_andamento"
    db_session.commit()

    response = integration_client.put(f"/routes/{route_id}", json={"name": "X"}, headers=headers)

    assert response.status_code == 409


def test_integration_update_route_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver1, _ = make_driver_with_vehicle(db_session)
    driver2, _ = make_driver_with_vehicle(db_session)

    create_response = integration_client.post(
        "/routes/", json=route_payload(),
        headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"},
    )
    route_id = create_response.json()["id"]

    response = integration_client.put(
        f"/routes/{route_id}", json={"name": "X"},
        headers={"X-User-Id": str(driver2.id), "X-User-Role": "driver"},
    )

    assert response.status_code == 403


def test_integration_update_route_partial_preserves_unchanged_fields(integration_client, db_session) -> None:
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]
    original_recurrence = create_response.json()["recurrence"]

    response = integration_client.put(f"/routes/{route_id}", json={"name": "Só o nome"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Só o nome"
    assert response.json()["recurrence"] == original_recurrence


# ===========================================================================
# US07 - TK-S05: GET /routes/{id} deve retornar as stops da rota
# Arquivo:       src/domains/routes/dtos.py (RouteResponse.stops) + controller.py
# ===========================================================================


def test_get_route_response_has_stops_field() -> None:
    """GET /routes/{id} deve retornar um campo 'stops' no body (default []))."""
    route_id = uuid.uuid4()
    mock_service = Mock(spec=RouteService)
    mock_service.get_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{route_id}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert "stops" in body
    assert isinstance(body["stops"], list)


def test_integration_get_route_without_passangers_returns_empty_stops(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} sem passageiros aceitos deve retornar stops=[]."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = create_response.json()["id"]

    response = integration_client.get(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["stops"] == []


def test_integration_get_route_with_stops_returns_all_stops(integration_client, db_session) -> None:
    """[Integração] GET /routes/{id} com stops persistidas deve retorná-las."""
    from src.domains.addresses.entity import AddressModel
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.domains.stops.entity import StopModel
    from src.domains.users.entity import UserModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_response = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = uuid.UUID(create_response.json()["id"])

    passenger = UserModel(
        name="Passageiro",
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="11988888888",
        password_hash="hashed",
        role="passanger",
    )
    db_session.add(passenger)
    db_session.flush()

    pickup = AddressModel(
        user_id=passenger.id, label="Pickup", street="R.1", number="1",
        neighborhood="N", zip="00000-000", city="POA", state="RS",
    )
    db_session.add(pickup)
    db_session.flush()

    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=passenger.id,
        pickup_address_id=pickup.id,
        status="accepted",
    )
    db_session.add(rp)
    db_session.flush()

    db_session.add(
        StopModel(
            route_id=route_id,
            route_passanger_id=rp.id,
            address_id=pickup.id,
            order_index=1,
            type="embarque",
        )
    )
    db_session.commit()

    response = integration_client.get(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["stops"]) == 1


def test_integration_list_routes_include_stops_field(integration_client, db_session) -> None:
    """[Integração] GET /routes/ deve retornar cada rota com campo stops."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    integration_client.post("/routes/", json=route_payload(), headers=headers)

    response = integration_client.get("/routes/", headers=headers)

    assert response.status_code == 200
    routes = response.json()
    assert len(routes) == 1
    assert "stops" in routes[0]
    assert routes[0]["stops"] == []


# ===========================================================================
# US08-TK06 — GET /routes/invite/{invite_code} (unit + integration)
# ===========================================================================


@pytest.mark.skip(reason="US08-TK06")
def test_get_by_invite_code_unit_returns_summary() -> None:
    """[Unit] Controller chama service.get_invite_summary e retorna o DTO."""
    from src.domains.routes.dtos import RouteInviteSummaryResponse

    summary_payload = {
        "id": str(uuid.uuid4()),
        "name": "PUCRS",
        "route_type": "outbound",
        "recurrence": "seg,ter,qua,qui,sex",
        "expected_time": "08:00:00",
        "max_passengers": 5,
        "accepted_count": 2,
        "origin_address": {
            "id": str(uuid.uuid4()),
            "label": "Casa",
            "street": "Rua 1",
            "number": "1",
            "neighborhood": "X",
            "zip": "00000-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "destination_address": {
            "id": str(uuid.uuid4()),
            "label": "PUCRS",
            "street": "Rua 2",
            "number": "2",
            "neighborhood": "Y",
            "zip": "00000-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
    }
    summary = RouteInviteSummaryResponse(**summary_payload)

    svc = Mock(spec=RouteService)
    svc.get_invite_summary.return_value = summary

    app.dependency_overrides[get_route_service] = lambda: svc
    try:
        response = client.get("/routes/invite/A1B2C", headers=DRIVER_HEADERS)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    svc.get_invite_summary.assert_called_once_with("A1B2C")
    body = response.json()
    assert body["accepted_count"] == 2
    assert body["name"] == "PUCRS"
    assert "invite_code" not in body
    assert "status" not in body
    assert "stops" not in body


@pytest.mark.skip(reason="US08-TK06")
def test_get_by_invite_code_unit_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    svc = Mock(spec=RouteService)
    svc.get_invite_summary.side_effect = RouteNotFoundError()

    app.dependency_overrides[get_route_service] = lambda: svc
    try:
        response = client.get("/routes/invite/ZZZZZ", headers=DRIVER_HEADERS)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.skip(reason="US08-TK06")
def test_integration_get_by_invite_code_success(integration_client, db_session) -> None:
    """[Integração] Criar rota, fazer GET /routes/invite/{code} e validar payload."""
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    create_resp = integration_client.post("/routes/", json=route_payload(), headers=headers)
    invite_code = create_resp.json()["invite_code"]

    response = integration_client.get(f"/routes/invite/{invite_code}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "PUCRS"
    assert body["accepted_count"] == 0
    assert body["max_passengers"] == 5
    assert "invite_code" not in body
    assert "status" not in body
    assert "stops" not in body


@pytest.mark.skip(reason="US08-TK06")
def test_integration_get_by_invite_code_not_found_returns_404(integration_client, db_session) -> None:
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.get("/routes/invite/ZZZZZ", headers=headers)
    assert response.status_code == 404


@pytest.mark.skip(reason="US08-TK06")
def test_integration_get_by_invite_code_counts_accepted_passangers(integration_client, db_session) -> None:
    """Cria rota + dois RPs aceitos + um pending → accepted_count = 2."""
    from src.domains.route_passangers.entity import RoutePassangerModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}
    create_resp = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = uuid.UUID(create_resp.json()["id"])
    invite_code = create_resp.json()["invite_code"]

    pickup_addr_id = uuid.UUID(create_resp.json()["origin_address"]["id"])
    for status in ("accepted", "accepted", "pending"):
        passenger = UserModel(
            name=f"P {status}",
            email=f"p_{uuid.uuid4().hex[:6]}@t.com",
            phone="11900000000",
            password_hash="h",
            role="guardian",
        )
        db_session.add(passenger)
        db_session.flush()
        db_session.add(RoutePassangerModel(
            route_id=route_id,
            user_id=passenger.id,
            pickup_address_id=pickup_addr_id,
            status=status,
        ))
    db_session.commit()

    response = integration_client.get(f"/routes/invite/{invite_code}", headers=headers)
    assert response.status_code == 200
    assert response.json()["accepted_count"] == 2


# ===========================================================================
# US06-TK19 — DELETE /routes/{route_id} — excluir rota
# ===========================================================================


def test_delete_route_success_returns_204() -> None:
    mock_service = Mock(spec=RouteService)
    mock_service.delete_route.return_value = None
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.delete(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 204
    mock_service.delete_route.assert_called_once()


def test_delete_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.delete_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.delete(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_delete_route_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.delete_route.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.delete(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_delete_route_in_progress_returns_409() -> None:
    from src.domains.routes.errors import RouteInProgressError

    mock_service = Mock(spec=RouteService)
    mock_service.delete_route.side_effect = RouteInProgressError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.delete(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 409


# --- Integração ---


def test_integration_delete_route_success(integration_client, db_session) -> None:
    from src.domains.routes.entity import RouteModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}
    create_resp = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = uuid.UUID(create_resp.json()["id"])

    response = integration_client.delete(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 204
    remaining = db_session.query(RouteModel).filter_by(id=route_id).first()
    assert remaining is None


def test_integration_delete_route_not_found_returns_404(integration_client, db_session) -> None:
    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}

    response = integration_client.delete(f"/routes/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


def test_integration_delete_route_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver1, _ = make_driver_with_vehicle(db_session)
    driver2, _ = make_driver_with_vehicle(db_session)
    create_resp = integration_client.post(
        "/routes/",
        json=route_payload(),
        headers={"X-User-Id": str(driver1.id), "X-User-Role": "driver"},
    )
    route_id = uuid.UUID(create_resp.json()["id"])

    response = integration_client.delete(
        f"/routes/{route_id}",
        headers={"X-User-Id": str(driver2.id), "X-User-Role": "driver"},
    )

    assert response.status_code == 403


def test_integration_delete_route_in_progress_returns_409(integration_client, db_session) -> None:
    from src.domains.routes.entity import RouteModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}
    create_resp = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = uuid.UUID(create_resp.json()["id"])

    route = db_session.query(RouteModel).filter_by(id=route_id).first()
    route.status = "em_andamento"
    db_session.commit()

    response = integration_client.delete(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 409


def test_integration_delete_route_cascades_passangers(integration_client, db_session) -> None:
    """Ao deletar rota, route_passangers e stops associadas são removidos via cascade."""
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.domains.stops.entity import StopModel

    driver, _ = make_driver_with_vehicle(db_session)
    headers = {"X-User-Id": str(driver.id), "X-User-Role": "driver"}
    create_resp = integration_client.post("/routes/", json=route_payload(), headers=headers)
    route_id = uuid.UUID(create_resp.json()["id"])
    pickup_addr_id = uuid.UUID(create_resp.json()["origin_address"]["id"])

    passenger = UserModel(
        name="Passageiro",
        email=f"p_{uuid.uuid4().hex[:6]}@t.com",
        phone="11900000000",
        password_hash="h",
        role="guardian",
    )
    db_session.add(passenger)
    db_session.flush()
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=passenger.id,
        pickup_address_id=pickup_addr_id,
        status="accepted",
    )
    db_session.add(rp)
    db_session.flush()
    stop = StopModel(
        route_id=route_id,
        route_passanger_id=rp.id,
        address_id=pickup_addr_id,
        type="embarque",
        order_index=0,
    )
    db_session.add(stop)
    db_session.commit()

    response = integration_client.delete(f"/routes/{route_id}", headers=headers)

    assert response.status_code == 204
    assert db_session.query(RoutePassangerModel).filter_by(route_id=route_id).first() is None
    assert db_session.query(StopModel).filter_by(route_id=route_id).first() is None
