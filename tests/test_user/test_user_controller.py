import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.domains.users.dtos import UserResponse
from src.domains.users.errors import DuplicateEmailError, UserNotFoundError
from src.domains.users.service import UserService
from src.infrastructure.dependencies.user_dependencies import get_user_service
from src.main import app


def make_user_response(**kwargs) -> UserResponse:
    defaults = {
        "id": uuid4(),
        "name": "John Doe",
        "email": "john@email.com",
        "phone": "54999999999",
        "role": "driver",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return UserResponse(**defaults)


# ===========================================================================
# US01 - TK04: POST /users/ — cadastro de usuário
# Arquivo: src/domains/users/controller.py
# ===========================================================================


# Teste 1: happy path — 201 com UserResponse
def test_register_user_success():
    """POST /users/ com dados válidos deve retornar 201 e o UserResponse."""
    mock_service = Mock(spec=UserService)
    mock_service.create_user.return_value = make_user_response()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.post("/users/", json={
        "name": "John Doe",
        "email": "john@email.com",
        "phone": "54999999999",
        "password": "senha123",
        "role": "driver",
    })

    assert response.status_code == 201
    assert response.json()["email"] == "john@email.com"

    app.dependency_overrides.clear()


# Teste 2: e-mail duplicado retorna 400
def test_register_user_duplicate_email_returns_400():
    """POST /users/ com e-mail já cadastrado deve retornar 400."""
    mock_service = Mock(spec=UserService)
    mock_service.create_user.side_effect = DuplicateEmailError()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.post("/users/", json={
        "name": "John Doe",
        "email": "john@email.com",
        "phone": "54999999999",
        "password": "senha123",
        "role": "driver",
    })

    assert response.status_code == 400

    app.dependency_overrides.clear()


# Teste 3: campos obrigatórios ausentes retornam 422 (Pydantic)
def test_register_user_missing_fields_returns_422():
    """POST /users/ sem campos obrigatórios deve retornar 422."""
    mock_service = Mock(spec=UserService)

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.post("/users/", json={})

    assert response.status_code == 422
    mock_service.create_user.assert_not_called()

    app.dependency_overrides.clear()


# Teste 4: role inválido retorna 422
def test_register_user_invalid_role_returns_422():
    """POST /users/ com role inválido deve retornar 422."""
    mock_service = Mock(spec=UserService)

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.post("/users/", json={
        "name": "John Doe",
        "email": "john@email.com",
        "phone": "54999999999",
        "password": "senha123",
        "role": "admin",
    })

    assert response.status_code == 422
    mock_service.create_user.assert_not_called()

    app.dependency_overrides.clear()


# Teste 5: motorista cadastrado com cpf — campo presente na resposta
def test_register_user_with_cpf_returns_cpf_in_response():
    """POST /users/ com cpf deve retornar 201 e cpf visível na resposta."""
    mock_service = Mock(spec=UserService)
    mock_service.create_user.return_value = make_user_response(cpf="999.999.999-99")

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.post("/users/", json={
        "name": "João Motorista",
        "email": "joao@email.com",
        "phone": "54999999999",
        "password": "senha123",
        "role": "driver",
        "cpf": "999.999.999-99",
    })

    assert response.status_code == 201
    assert response.json()["cpf"] == "999.999.999-99"

    app.dependency_overrides.clear()


# ===========================================================================
# US02 - TK04: GET / PUT / DELETE /users/{user_id}
# ===========================================================================

# --- US02-TK04: implementar GET/PUT/DELETE em src/domains/users/controller.py ---
# Para ativar: remova @pytest.mark.skip dos testes abaixo

# ---- GET /users/{user_id} ----

# Teste 1: retorna 200 com UserResponse quando usuário existe
@pytest.mark.skip(reason="US02-TK04")
def test_get_user_success():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.get_user.return_value = make_user_response()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["email"] == "john@email.com"

    app.dependency_overrides.clear()


# Teste 2: retorna 404 quando usuário não existe
@pytest.mark.skip(reason="US02-TK04")
def test_get_user_not_found():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.get_user.side_effect = UserNotFoundError()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 404

    app.dependency_overrides.clear()


# ---- PUT /users/{user_id} ----

# Teste 3: retorna 200 com dados atualizados
@pytest.mark.skip(reason="US02-TK04")
def test_update_user_success():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.update_user.return_value = make_user_response(name="Updated Name")

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.put(f"/users/{user_id}", json={"name": "Updated Name"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

    app.dependency_overrides.clear()


# Teste 4: retorna 404 quando usuário não existe
@pytest.mark.skip(reason="US02-TK04")
def test_update_user_not_found():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.update_user.side_effect = UserNotFoundError()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.put(f"/users/{user_id}", json={"name": "Updated Name"})

    assert response.status_code == 404

    app.dependency_overrides.clear()


# Teste 5: campo vazio no payload retorna 422 (Pydantic rejeita antes de chegar no service)
@pytest.mark.skip(reason="US02-TK04")
def test_update_user_invalid_payload():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.put(f"/users/{user_id}", json={"name": ""})

    assert response.status_code == 422
    mock_service.update_user.assert_not_called()

    app.dependency_overrides.clear()


# ---- DELETE /users/{user_id} ----

# Teste 6: retorna 204 No Content quando exclusão ocorre com sucesso
@pytest.mark.skip(reason="US02-TK04")
def test_delete_user_success():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.delete_user.return_value = None

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 204

    app.dependency_overrides.clear()


# Teste 7: retorna 404 quando usuário não existe
@pytest.mark.skip(reason="US02-TK04")
def test_delete_user_not_found():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.delete_user.side_effect = UserNotFoundError()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 404

    app.dependency_overrides.clear()
