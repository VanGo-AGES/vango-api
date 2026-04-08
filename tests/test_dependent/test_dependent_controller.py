"""
US03 - TK04: Implementar Endpoints de Criação (DependentController)
Arquivo: src/domains/dependents/controller.py

Testes de integração HTTP para POST /dependents/.
Verifica status codes, payloads de resposta e tratamento de erros.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.domains.dependents.entity import DependentModel
from src.domains.dependents.errors import DependentAccessDeniedError
from src.domains.dependents.service import DependentService
from src.infrastructure.dependencies.auth_dependencies import get_current_user
from src.infrastructure.dependencies.dependent_dependencies import get_dependent_service
from src.main import app


def make_mock_dependent(name: str = "Ana") -> DependentModel:
    return DependentModel(
        id=uuid.uuid4(),
        guardian_id=uuid.uuid4(),
        name=name,
        created_at=datetime.now(),
    )


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_create_dependent_passenger_success(client):
    """POST /dependents/ com role 'passenger' deve retornar 201 Created."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.return_value = make_mock_dependent()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"name": "Ana"})

    app.dependency_overrides.clear()

    assert response.status_code == 201


def test_create_dependent_guardian_success(client):
    """POST /dependents/ com role 'guardian' deve retornar 201 Created."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.return_value = make_mock_dependent()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "guardian"}

    response = client.post("/dependents/", json={"name": "Pedro"})

    app.dependency_overrides.clear()

    assert response.status_code == 201


def test_create_dependent_response_has_correct_fields(client):
    """Resposta 201 deve conter id, name, guardian_id e created_at."""
    dependent = make_mock_dependent()
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.return_value = dependent

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"name": "Ana"})

    app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert "name" in body
    assert "guardian_id" in body
    assert "created_at" in body


# ---------------------------------------------------------------------------
# Role não autorizada — 403 Forbidden
# ---------------------------------------------------------------------------


def test_create_dependent_driver_returns_403(client):
    """POST /dependents/ com role 'driver' deve retornar 403 Forbidden."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.side_effect = DependentAccessDeniedError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "driver"}

    response = client.post("/dependents/", json={"name": "Ana"})

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Payload inválido — 422 Unprocessable Entity
# ---------------------------------------------------------------------------


def test_create_dependent_missing_name_returns_422(client):
    """Payload sem name deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_dependent_empty_name_returns_422(client):
    """name vazio deve ser rejeitado com 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"name": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_create_dependent_invalid_payload_returns_422(client):
    """Payload com campos incorretos deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"invalid_field": "value"})

    app.dependency_overrides.clear()

    assert response.status_code == 422


# ===========================================================================
# US04 - TK04: Implementar Endpoints de Visualização, Edição e Exclusão
# ===========================================================================

from src.domains.dependents.errors import DependentNotFoundError, DependentOwnershipError


def make_dependent_list() -> list[DependentModel]:
    return [
        DependentModel(id=uuid.uuid4(), guardian_id=uuid.uuid4(), name="Ana", created_at=datetime.now()),
        DependentModel(id=uuid.uuid4(), guardian_id=uuid.uuid4(), name="Pedro", created_at=datetime.now()),
    ]


# ---------------------------------------------------------------------------
# GET /dependents/
# ---------------------------------------------------------------------------


def test_list_dependents_success(client):
    """GET /dependents/ deve retornar 200 com lista de dependentes."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependents.return_value = make_dependent_list()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get("/dependents/")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


def test_list_dependents_empty(client):
    """GET /dependents/ deve retornar 200 com lista vazia quando não há dependentes."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependents.return_value = []

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get("/dependents/")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_get_dependent_by_id_success(client):
    """GET /dependents/{id} deve retornar 200 com o dependente do usuário."""
    dependent = make_mock_dependent()
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependent.return_value = dependent

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get(f"/dependents/{dependent.id}")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(dependent.id)


def test_get_dependent_not_found_returns_404(client):
    """GET /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_dependent_wrong_owner_returns_403(client):
    """GET /dependents/{id} deve retornar 403 quando pertence a outro guardião."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependent.side_effect = DependentOwnershipError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_update_dependent_success(client):
    """PUT /dependents/{id} deve retornar 200 com o dependente atualizado."""
    dependent = make_mock_dependent(name="Ana Paula")
    mock_service = MagicMock(spec=DependentService)
    mock_service.update_dependent.return_value = dependent

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{dependent.id}", json={"name": "Ana Paula"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["name"] == "Ana Paula"


def test_update_dependent_not_found_returns_404(client):
    """PUT /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.update_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": "Novo"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_update_dependent_wrong_owner_returns_403(client):
    """PUT /dependents/{id} deve retornar 403 quando pertence a outro guardião."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.update_dependent.side_effect = DependentOwnershipError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": "Novo"})

    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_update_dependent_empty_name_returns_422(client):
    """PUT /dependents/{id} com name vazio deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_delete_dependent_success(client):
    """DELETE /dependents/{id} deve retornar 204 No Content."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.return_value = None

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 204


def test_delete_dependent_not_found_returns_404(client):
    """DELETE /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_delete_dependent_wrong_owner_returns_403(client):
    """DELETE /dependents/{id} deve retornar 403 quando pertence a outro guardião."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.side_effect = DependentOwnershipError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 403


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db e get_current_user.
# ===========================================================================

from src.domains.users.entity import UserModel
from src.infrastructure.database import get_db
from src.infrastructure.repositories.dependent_repository import DependentRepositoryImpl


def make_guardian_in_db(db_session, role: str = "passenger") -> UserModel:
    user = UserModel(
        name="Guardião Integração",
        email=f"guardian_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role=role,
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
# POST /dependents/
# ---------------------------------------------------------------------------


def test_integration_create_dependent_passenger_success(integration_client, db_session):
    """[Integração] POST /dependents/ com role passenger deve persistir e retornar 201."""
    guardian = make_guardian_in_db(db_session, role="passenger")
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.post("/dependents/", json={"name": "Ana"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ana"
    assert body["guardian_id"] == str(guardian.id)


def test_integration_create_dependent_guardian_success(integration_client, db_session):
    """[Integração] POST /dependents/ com role guardian deve persistir e retornar 201."""
    guardian = make_guardian_in_db(db_session, role="guardian")
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "guardian"}

    response = integration_client.post("/dependents/", json={"name": "Pedro"})

    assert response.status_code == 201
    assert response.json()["guardian_id"] == str(guardian.id)


def test_integration_create_dependent_driver_returns_403(integration_client, db_session):
    """[Integração] POST /dependents/ com role driver deve retornar 403."""
    driver = UserModel(
        name="Motorista",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    app.dependency_overrides[get_current_user] = lambda: {"id": str(driver.id), "role": "driver"}

    response = integration_client.post("/dependents/", json={"name": "Ana"})

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /dependents/
# ---------------------------------------------------------------------------


def test_integration_list_dependents_empty(integration_client, db_session):
    """[Integração] GET /dependents/ sem dependentes deve retornar 200 com lista vazia."""
    guardian = make_guardian_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.get("/dependents/")

    assert response.status_code == 200
    assert response.json() == []


def test_integration_list_dependents_returns_own_only(integration_client, db_session):
    """[Integração] GET /dependents/ deve retornar apenas dependentes do guardião autenticado."""
    guardian1 = make_guardian_in_db(db_session)
    guardian2 = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    repo.create(DependentModel(guardian_id=guardian1.id, name="Filho G1"))
    repo.create(DependentModel(guardian_id=guardian2.id, name="Filho G2"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian1.id), "role": "passenger"}

    response = integration_client.get("/dependents/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Filho G1"


# ---------------------------------------------------------------------------
# GET /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_integration_get_dependent_by_id_success(integration_client, db_session):
    """[Integração] GET /dependents/{id} deve retornar 200 com dados do dependente."""
    guardian = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian.id, name="Maria"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.get(f"/dependents/{dependent.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Maria"


def test_integration_get_dependent_not_found_returns_404(integration_client, db_session):
    """[Integração] GET /dependents/{id} com id inexistente deve retornar 404."""
    guardian = make_guardian_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.get(f"/dependents/{uuid.uuid4()}")

    assert response.status_code == 404


def test_integration_get_dependent_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] GET /dependents/{id} por guardião diferente do dono deve retornar 403."""
    guardian1 = make_guardian_in_db(db_session)
    guardian2 = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian1.id, name="Lucas"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian2.id), "role": "passenger"}

    response = integration_client.get(f"/dependents/{dependent.id}")

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_integration_update_dependent_success(integration_client, db_session):
    """[Integração] PUT /dependents/{id} deve atualizar e retornar 200 com dados novos."""
    guardian = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian.id, name="Ana"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.put(f"/dependents/{dependent.id}", json={"name": "Ana Paula"})

    assert response.status_code == 200
    assert response.json()["name"] == "Ana Paula"


def test_integration_update_dependent_not_found_returns_404(integration_client, db_session):
    """[Integração] PUT /dependents/{id} com id inexistente deve retornar 404."""
    guardian = make_guardian_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.put(f"/dependents/{uuid.uuid4()}", json={"name": "Novo"})

    assert response.status_code == 404


def test_integration_update_dependent_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] PUT /dependents/{id} por guardião diferente do dono deve retornar 403."""
    guardian1 = make_guardian_in_db(db_session)
    guardian2 = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian1.id, name="Julia"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian2.id), "role": "passenger"}

    response = integration_client.put(f"/dependents/{dependent.id}", json={"name": "Novo"})

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /dependents/{dependent_id}
# ---------------------------------------------------------------------------


def test_integration_delete_dependent_success(integration_client, db_session):
    """[Integração] DELETE /dependents/{id} deve remover do banco e retornar 204."""
    guardian = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian.id, name="Carla"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.delete(f"/dependents/{dependent.id}")

    assert response.status_code == 204


def test_integration_delete_dependent_not_found_returns_404(integration_client, db_session):
    """[Integração] DELETE /dependents/{id} com id inexistente deve retornar 404."""
    guardian = make_guardian_in_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian.id), "role": "passenger"}

    response = integration_client.delete(f"/dependents/{uuid.uuid4()}")

    assert response.status_code == 404


def test_integration_delete_dependent_wrong_owner_returns_403(integration_client, db_session):
    """[Integração] DELETE /dependents/{id} por guardião diferente do dono deve retornar 403."""
    guardian1 = make_guardian_in_db(db_session)
    guardian2 = make_guardian_in_db(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = repo.create(DependentModel(guardian_id=guardian1.id, name="Roberto"))
    app.dependency_overrides[get_current_user] = lambda: {"id": str(guardian2.id), "role": "passenger"}

    response = integration_client.delete(f"/dependents/{dependent.id}")

    assert response.status_code == 403
