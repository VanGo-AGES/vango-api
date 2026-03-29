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


@pytest.mark.skip(reason="US03-TK04")
def test_create_dependent_passenger_success(client):
    """POST /dependents/ com role 'passenger' deve retornar 201 Created."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.return_value = make_mock_dependent()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"name": "Ana"})

    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.skip(reason="US03-TK04")
def test_create_dependent_guardian_success(client):
    """POST /dependents/ com role 'guardian' deve retornar 201 Created."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.add_dependent.return_value = make_mock_dependent()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "guardian"}

    response = client.post("/dependents/", json={"name": "Pedro"})

    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.skip(reason="US03-TK04")
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


@pytest.mark.skip(reason="US03-TK04")
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


@pytest.mark.skip(reason="US03-TK04")
def test_create_dependent_missing_name_returns_422(client):
    """Payload sem name deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={})

    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.skip(reason="US03-TK04")
def test_create_dependent_empty_name_returns_422(client):
    """name vazio deve ser rejeitado com 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.post("/dependents/", json={"name": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.skip(reason="US03-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
def test_get_dependent_not_found_returns_404(client):
    """GET /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.get_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.get(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.skip(reason="US04-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
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


@pytest.mark.skip(reason="US04-TK04")
def test_update_dependent_not_found_returns_404(client):
    """PUT /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.update_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": "Novo"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.skip(reason="US04-TK04")
def test_update_dependent_wrong_owner_returns_403(client):
    """PUT /dependents/{id} deve retornar 403 quando pertence a outro guardião."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.update_dependent.side_effect = DependentOwnershipError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": "Novo"})

    app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.skip(reason="US04-TK04")
def test_update_dependent_empty_name_returns_422(client):
    """PUT /dependents/{id} com name vazio deve retornar 422."""
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.put(f"/dependents/{uuid.uuid4()}", json={"name": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /dependents/{dependent_id}
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US04-TK04")
def test_delete_dependent_success(client):
    """DELETE /dependents/{id} deve retornar 204 No Content."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.return_value = None

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 204


@pytest.mark.skip(reason="US04-TK04")
def test_delete_dependent_not_found_returns_404(client):
    """DELETE /dependents/{id} deve retornar 404 quando dependente não existe."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.side_effect = DependentNotFoundError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.skip(reason="US04-TK04")
def test_delete_dependent_wrong_owner_returns_403(client):
    """DELETE /dependents/{id} deve retornar 403 quando pertence a outro guardião."""
    mock_service = MagicMock(spec=DependentService)
    mock_service.delete_dependent.side_effect = DependentOwnershipError()

    app.dependency_overrides[get_dependent_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid.uuid4()), "role": "passenger"}

    response = client.delete(f"/dependents/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 403
