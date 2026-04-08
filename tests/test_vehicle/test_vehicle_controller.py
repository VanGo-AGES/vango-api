"""
US03 - TK04: Implementar Endpoints de Criação (VehicleController)
Arquivo: src/domains/vehicles/controller.py

Testes de integração HTTP para POST /vehicles/.
Verifica status codes, payloads de resposta e tratamento de erros.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.errors import VehicleAccessDeniedError
from src.domains.vehicles.service import VehicleService
from src.infrastructure.dependencies.auth_dependencies import get_current_user
from src.infrastructure.dependencies.vehicle_dependencies import get_vehicle_service
from src.main import app


def make_mock_vehicle(plate: str = "ABC1D23", capacity: int = 4) -> VehicleModel:
    return VehicleModel(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        plate=plate,
        capacity=capacity,
        notes=None,
        status=True,
        created_at=datetime.now(),
    )


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_create_vehicle_driver_success(client):
    """POST /vehicles/ com role 'driver' deve retornar 201 Created."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.add_vehicle.return_value = make_mock_vehicle()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 201


def test_create_vehicle_response_has_correct_fields(client):
    """Resposta 201 deve conter id, plate, capacity, driver_id, status e created_at."""
    vehicle = make_mock_vehicle()
    mock_service = MagicMock(spec=VehicleService)
    mock_service.add_vehicle.return_value = vehicle

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert "plate" in body
    assert "capacity" in body
    assert "driver_id" in body
    assert "status" in body
    assert "created_at" in body


def test_create_vehicle_with_notes_success(client):
    """POST com notes preenchido deve retornar 201 e incluir notes na resposta."""
    vehicle = make_mock_vehicle()
    vehicle.notes = "Ar condicionado"
    mock_service = MagicMock(spec=VehicleService)
    mock_service.add_vehicle.return_value = vehicle

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 4, "notes": "Ar condicionado"})

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["notes"] == "Ar condicionado"


# ---------------------------------------------------------------------------
# Roles não autorizadas — 403 Forbidden
# ---------------------------------------------------------------------------


def test_create_vehicle_passenger_returns_403(client):
    """POST /vehicles/ com role 'passenger' deve retornar 403 Forbidden."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.add_vehicle.side_effect = VehicleAccessDeniedError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_create_vehicle_guardian_returns_403(client):
    """POST /vehicles/ com role 'guardian' deve retornar 403 Forbidden."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.add_vehicle.side_effect = VehicleAccessDeniedError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "guardian"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Payload inválido — 422 Unprocessable Entity
# ---------------------------------------------------------------------------


def test_create_vehicle_missing_plate_returns_422(client):
    """Payload sem plate deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_vehicle_missing_capacity_returns_422(client):
    """Payload sem capacity deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23"})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_vehicle_empty_payload_returns_422(client):
    """Payload vazio deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_vehicle_empty_plate_returns_422(client):
    """Plate vazia deve ser rejeitada com 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "", "capacity": 4})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_vehicle_zero_capacity_returns_422(client):
    """Capacity igual a zero deve ser rejeitada com 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/vehicles/", json={"plate": "ABC1D23", "capacity": 0})

    app.dependency_overrides.clear()

    assert response.status_code == 422


# ===========================================================================
# US04 - TK04: Implementar Endpoints de Visualização, Edição e Exclusão
# ===========================================================================

from src.domains.vehicles.errors import VehicleNotFoundError, VehicleOwnershipError


def make_vehicle_list() -> list[VehicleModel]:
    return [
        VehicleModel(id=uuid.uuid4(), driver_id=uuid.uuid4(), plate="L01", capacity=4, status=True, created_at=datetime.now()),
        VehicleModel(id=uuid.uuid4(), driver_id=uuid.uuid4(), plate="L02", capacity=6, status=True, created_at=datetime.now()),
    ]


# ---------------------------------------------------------------------------
# GET /vehicles/
# ---------------------------------------------------------------------------


def test_list_vehicles_success(client):
    """GET /vehicles/ deve retornar 200 com lista de veículos."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.get_vehicles.return_value = make_vehicle_list()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.get("/vehicles/")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


def test_list_vehicles_empty(client):
    """GET /vehicles/ deve retornar 200 com lista vazia quando não há veículos."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.get_vehicles.return_value = []

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.get("/vehicles/")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_get_vehicle_by_id_success(client):
    """GET /vehicles/{id} deve retornar 200 com o veículo do usuário."""
    vehicle = make_mock_vehicle()
    mock_service = MagicMock(spec=VehicleService)
    mock_service.get_vehicle.return_value = vehicle

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.get(f"/vehicles/{vehicle.id}")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(vehicle.id)


def test_get_vehicle_not_found_returns_404(client):
    """GET /vehicles/{id} deve retornar 404 quando veículo não existe."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.get_vehicle.side_effect = VehicleNotFoundError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.get(f"/vehicles/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_vehicle_wrong_owner_returns_403(client):
    """GET /vehicles/{id} deve retornar 403 quando veículo pertence a outro driver."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.get_vehicle.side_effect = VehicleOwnershipError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.get(f"/vehicles/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_update_vehicle_success(client):
    """PUT /vehicles/{id} deve retornar 200 com o veículo atualizado."""
    vehicle = make_mock_vehicle(plate="NEW0001", capacity=6)
    mock_service = MagicMock(spec=VehicleService)
    mock_service.update_vehicle.return_value = vehicle

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.put(f"/vehicles/{vehicle.id}", json={"plate": "NEW0001", "capacity": 6})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["plate"] == "NEW0001"


def test_update_vehicle_not_found_returns_404(client):
    """PUT /vehicles/{id} deve retornar 404 quando veículo não existe."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.update_vehicle.side_effect = VehicleNotFoundError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.put(f"/vehicles/{uuid.uuid4()}", json={"plate": "X"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_update_vehicle_wrong_owner_returns_403(client):
    """PUT /vehicles/{id} deve retornar 403 quando pertence a outro driver."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.update_vehicle.side_effect = VehicleOwnershipError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.put(f"/vehicles/{uuid.uuid4()}", json={"plate": "X"})

    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_update_vehicle_invalid_payload_returns_422(client):
    """PUT /vehicles/{id} com capacity inválida deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.put(f"/vehicles/{uuid.uuid4()}", json={"capacity": -1})

    app.dependency_overrides.clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_delete_vehicle_success(client):
    """DELETE /vehicles/{id} deve retornar 204 No Content."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.delete_vehicle.return_value = None

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.delete(f"/vehicles/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 204


def test_delete_vehicle_not_found_returns_404(client):
    """DELETE /vehicles/{id} deve retornar 404 quando veículo não existe."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.delete_vehicle.side_effect = VehicleNotFoundError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.delete(f"/vehicles/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_delete_vehicle_wrong_owner_returns_403(client):
    """DELETE /vehicles/{id} deve retornar 403 quando pertence a outro driver."""
    mock_service = MagicMock(spec=VehicleService)
    mock_service.delete_vehicle.side_effect = VehicleOwnershipError()

    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.delete(f"/vehicles/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db e get_current_user.
# ===========================================================================

from src.domains.users.entity import UserModel
from src.infrastructure.database import get_db
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl


def make_driver_in_db(db_session) -> UserModel:
    user = UserModel(
        name="Driver Integração",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /vehicles/
# ---------------------------------------------------------------------------


def test_integration_create_vehicle_driver_success(integration_client, db_session):
    """[Integração] POST /vehicles/ com driver real deve persistir e retornar 201."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.post("/vehicles/", json={"plate": "ITG0001", "capacity": 4})

    assert response.status_code == 201
    body = response.json()
    assert body["plate"] == "ITG0001"
    assert body["driver_id"] == str(driver.id)


def test_integration_create_vehicle_with_notes(integration_client, db_session):
    """[Integração] POST /vehicles/ com notes deve persistir o campo no banco."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.post(
        "/vehicles/", json={"plate": "ITG0002", "capacity": 4, "notes": "Ar condicionado"}
    )

    assert response.status_code == 201
    assert response.json()["notes"] == "Ar condicionado"


def test_integration_create_vehicle_passenger_returns_403(integration_client, db_session):
    """[Integração] POST /vehicles/ com role passenger deve retornar 403."""
    user = UserModel(
        name="Passageiro",
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="passenger",
    )
    db_session.add(user)
    db_session.flush()
    app.dependency_overrides[get_current_user] = lambda: {"id": str(user.id), "role": "passenger"}

    response = integration_client.post("/vehicles/", json={"plate": "ITG0003", "capacity": 4})

    assert response.status_code == 403


def test_integration_create_vehicle_guardian_returns_403(integration_client, db_session):
    """[Integração] POST /vehicles/ com role guardian deve retornar 403."""
    user = UserModel(
        name="Guardião",
        email=f"guard_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="guardian",
    )
    db_session.add(user)
    db_session.flush()
    app.dependency_overrides[get_current_user] = lambda: {"id": str(user.id), "role": "guardian"}

    response = integration_client.post("/vehicles/", json={"plate": "ITG0004", "capacity": 4})

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /vehicles/
# ---------------------------------------------------------------------------


def test_integration_list_vehicles_empty(integration_client, db_session):
    """[Integração] GET /vehicles/ sem veículos deve retornar 200 com lista vazia."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.get("/vehicles/")

    assert response.status_code == 200
    assert response.json() == []


def test_integration_list_vehicles_returns_own_only(integration_client, db_session):
    """[Integração] GET /vehicles/ deve retornar apenas veículos do driver autenticado."""
    driver1 = make_driver_in_db(db_session)
    driver2 = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    repo.create(VehicleModel(driver_id=driver1.id, plate="LST0001", capacity=4))
    repo.create(VehicleModel(driver_id=driver2.id, plate="LST0002", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver1.id), "role": "driver"}

    response = integration_client.get("/vehicles/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["plate"] == "LST0001"


# ---------------------------------------------------------------------------
# GET /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_integration_get_vehicle_by_id_success(integration_client, db_session):
    """[Integração] GET /vehicles/{id} deve retornar 200 com dados do veículo."""
    driver = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver.id, plate="GET0001", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.get(f"/vehicles/{vehicle.id}")

    assert response.status_code == 200
    assert response.json()["plate"] == "GET0001"


def test_integration_get_vehicle_not_found_returns_404(integration_client, db_session):
    """[Integração] GET /vehicles/{id} com id inexistente deve retornar 404."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.get(f"/vehicles/{uuid.uuid4()}")

    assert response.status_code == 404


def test_integration_get_vehicle_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] GET /vehicles/{id} por driver diferente do dono deve retornar 403."""
    driver1 = make_driver_in_db(db_session)
    driver2 = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver1.id, plate="OWN0001", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver2.id), "role": "driver"}

    response = integration_client.get(f"/vehicles/{vehicle.id}")

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_integration_update_vehicle_success(integration_client, db_session):
    """[Integração] PUT /vehicles/{id} deve atualizar e retornar 200 com dados novos."""
    driver = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver.id, plate="UPD0001", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.put(f"/vehicles/{vehicle.id}", json={"capacity": 8})

    assert response.status_code == 200
    assert response.json()["capacity"] == 8


def test_integration_update_vehicle_not_found_returns_404(integration_client, db_session):
    """[Integração] PUT /vehicles/{id} com id inexistente deve retornar 404."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.put(f"/vehicles/{uuid.uuid4()}", json={"capacity": 8})

    assert response.status_code == 404


def test_integration_update_vehicle_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] PUT /vehicles/{id} por driver diferente do dono deve retornar 403."""
    driver1 = make_driver_in_db(db_session)
    driver2 = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver1.id, plate="UPD0002", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver2.id), "role": "driver"}

    response = integration_client.put(f"/vehicles/{vehicle.id}", json={"capacity": 8})

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /vehicles/{vehicle_id}
# ---------------------------------------------------------------------------


def test_integration_delete_vehicle_success(integration_client, db_session):
    """[Integração] DELETE /vehicles/{id} deve remover do banco e retornar 204."""
    driver = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver.id, plate="DEL0001", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.delete(f"/vehicles/{vehicle.id}")

    assert response.status_code == 204


def test_integration_delete_vehicle_not_found_returns_404(integration_client, db_session):
    """[Integração] DELETE /vehicles/{id} com id inexistente deve retornar 404."""
    driver = make_driver_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.delete(f"/vehicles/{uuid.uuid4()}")

    assert response.status_code == 404


def test_integration_delete_vehicle_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] DELETE /vehicles/{id} por driver diferente do dono deve retornar 403."""
    driver1 = make_driver_in_db(db_session)
    driver2 = make_driver_in_db(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = repo.create(VehicleModel(driver_id=driver1.id, plate="DEL0002", capacity=4))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver2.id), "role": "driver"}

    response = integration_client.delete(f"/vehicles/{vehicle.id}")

    assert response.status_code == 403
