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
# GET /users/ — listar todos os usuários
# ===========================================================================


# Teste 1: retorna 200 com lista de usuários
def test_list_users_returns_200_with_list():
    """GET /users/ deve retornar 200 e uma lista de UserResponse."""
    mock_service = Mock(spec=UserService)
    mock_service.list_users.return_value = [
        make_user_response(email="a@email.com"),
        make_user_response(email="b@email.com"),
    ]

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.get("/users/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2

    app.dependency_overrides.clear()


# Teste 2: retorna 200 com lista vazia quando não há usuários
def test_list_users_empty_returns_200_with_empty_list():
    """GET /users/ sem usuários cadastrados deve retornar 200 e lista vazia."""
    mock_service = Mock(spec=UserService)
    mock_service.list_users.return_value = []

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.get("/users/")

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


# ===========================================================================
# US02 - TK04: GET / PUT / DELETE /users/{user_id}
# ===========================================================================

# --- US02-TK04: implementar GET/PUT/DELETE em src/domains/users/controller.py ---
# Para ativar: remova @pytest.mark.skip dos testes abaixo

# ---- GET /users/{user_id} ----

# Teste 1: retorna 200 com UserResponse quando usuário existe
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
def test_delete_user_not_found():
    user_id = str(uuid4())
    mock_service = Mock(spec=UserService)
    mock_service.delete_user.side_effect = UserNotFoundError()

    app.dependency_overrides[get_user_service] = lambda: mock_service
    client = TestClient(app)

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 404

    app.dependency_overrides.clear()


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db.
# ===========================================================================

from src.infrastructure.database import get_db
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domains.users.entity import UserModel as UserModelEntity


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user_payload(**kwargs) -> dict:
    defaults = {
        "name": "João Silva",
        "email": f"joao_{uuid4()}@test.com",
        "phone": "54999999999",
        "password": "senha123",
        "role": "driver",
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# GET /users/
# ---------------------------------------------------------------------------


def test_integration_list_users_returns_all(integration_client):
    """[Integração] GET /users/ deve retornar 200 com todos os usuários cadastrados."""
    payload_a = make_user_payload()
    payload_b = make_user_payload()

    integration_client.post("/users/", json=payload_a)
    integration_client.post("/users/", json=payload_b)

    response = integration_client.get("/users/")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    emails = [u["email"] for u in body]
    assert payload_a["email"] in emails
    assert payload_b["email"] in emails


def test_integration_list_users_empty_returns_empty_list(integration_client):
    """[Integração] GET /users/ sem usuários deve retornar 200 e lista vazia."""
    response = integration_client.get("/users/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# POST /users/
# ---------------------------------------------------------------------------


def test_integration_register_user_success(integration_client):
    """[Integração] POST /users/ deve persistir e retornar 201 com dados do usuário."""
    payload = make_user_payload()

    response = integration_client.post("/users/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "driver"
    assert "id" in body
    assert "password" not in body


def test_integration_register_user_duplicate_email_returns_400(integration_client):
    """[Integração] POST /users/ com e-mail duplicado deve retornar 400."""
    payload = make_user_payload()
    integration_client.post("/users/", json=payload)

    response = integration_client.post("/users/", json=payload)

    assert response.status_code == 400


def test_integration_register_passenger_success(integration_client):
    """[Integração] POST /users/ com role passenger deve retornar 201."""
    payload = make_user_payload(role="passenger")

    response = integration_client.post("/users/", json=payload)

    assert response.status_code == 201
    assert response.json()["role"] == "passenger"


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US02-TK04")
def test_integration_get_user_success(integration_client, db_session):
    """[Integração] GET /users/{id} deve retornar 200 com dados do usuário."""
    repo = UserRepositoryImpl(db_session)
    user = repo.save(UserModelEntity(
        name="Maria",
        email=f"maria_{uuid4()}@test.com",
        phone="54999999999",
        password_hash="hashed",
        role="passenger",
    ))

    response = integration_client.get(f"/users/{user.id}")

    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.skip(reason="US02-TK04")
def test_integration_get_user_not_found_returns_404(integration_client):
    """[Integração] GET /users/{id} com id inexistente deve retornar 404."""
    response = integration_client.get(f"/users/{uuid4()}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US02-TK04")
def test_integration_update_user_success(integration_client, db_session):
    """[Integração] PUT /users/{id} deve atualizar e retornar 200 com novos dados."""
    repo = UserRepositoryImpl(db_session)
    user = repo.save(UserModelEntity(
        name="Carlos",
        email=f"carlos_{uuid4()}@test.com",
        phone="54999999999",
        password_hash="hashed",
        role="driver",
    ))

    response = integration_client.put(f"/users/{user.id}", json={"name": "Carlos Silva"})

    assert response.status_code == 200
    assert response.json()["name"] == "Carlos Silva"


@pytest.mark.skip(reason="US02-TK04")
def test_integration_update_user_not_found_returns_404(integration_client):
    """[Integração] PUT /users/{id} com id inexistente deve retornar 404."""
    response = integration_client.put(f"/users/{uuid4()}", json={"name": "Novo Nome"})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US02-TK04")
def test_integration_delete_user_success(integration_client, db_session):
    """[Integração] DELETE /users/{id} deve remover e retornar 204."""
    repo = UserRepositoryImpl(db_session)
    user = repo.save(UserModelEntity(
        name="Deletar",
        email=f"delete_{uuid4()}@test.com",
        phone="54999999999",
        password_hash="hashed",
        role="passenger",
    ))

    response = integration_client.delete(f"/users/{user.id}")

    assert response.status_code == 204


@pytest.mark.skip(reason="US02-TK04")
def test_integration_delete_user_not_found_returns_404(integration_client):
    """[Integração] DELETE /users/{id} com id inexistente deve retornar 404."""
    response = integration_client.delete(f"/users/{uuid4()}")

    assert response.status_code == 404
