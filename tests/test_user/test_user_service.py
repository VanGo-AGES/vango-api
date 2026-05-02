import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.domains.users.service import UserService
from src.domains.users.entity import UserModel
from src.domains.users.dtos import UserUpdate
from src.domains.users.dtos import UserCreate, UserUpdate
from src.domains.users.errors import (
    DuplicateEmailError,
    InvalidCredentialsError,
    UserNotFoundError,
)


# ===========================================================================
# US01 - TK03: UserService.create_user
# Arquivo: src/domains/users/service.py
# ===========================================================================


# Teste 1: happy path — usuário criado com sucesso e salvo no repositório
def test_create_user_success():
    """create_user deve verificar email, hashear senha e chamar repo.save."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = None
    hasher.hash.return_value = "hashed_password"
    repo.save.return_value = UserModel(
        name="John Doe",
        email="john@email.com",
        phone="54999999999",
        password_hash="hashed_password",
        role="driver",
    )

    service = UserService(repo, hasher)
    result = service.create_user(UserCreate(
        name="John Doe",
        email="john@email.com",
        phone="54999999999",
        password="senha123",
        role="driver",
    ))

    repo.find_by_email.assert_called_once_with("john@email.com")
    hasher.hash.assert_called_once_with("senha123")
    repo.save.assert_called_once()
    assert result.email == "john@email.com"


# Teste 2: e-mail duplicado — DuplicateEmailError, repo.save nunca chamado
def test_create_user_duplicate_email_raises_error():
    """create_user com e-mail já cadastrado deve lançar DuplicateEmailError."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = UserModel(
        name="Existing",
        email="john@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver",
    )

    service = UserService(repo, hasher)

    with pytest.raises(DuplicateEmailError):
        service.create_user(UserCreate(
            name="John Doe",
            email="john@email.com",
            phone="54999999999",
            password="senha123",
            role="driver",
        ))

    repo.save.assert_not_called()


# Teste 3: senha armazenada como hash, nunca em texto plano
def test_create_user_stores_password_hash():
    """O UserModel salvo deve ter password_hash, não a senha em texto plano."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = None
    hasher.hash.return_value = "hashed_secret"
    repo.save.return_value = Mock()

    service = UserService(repo, hasher)
    service.create_user(UserCreate(
        name="John Doe",
        email="john@email.com",
        phone="54999999999",
        password="plain_password",
        role="driver",
    ))

    saved_model = repo.save.call_args[0][0]

    assert saved_model.password_hash == "hashed_secret"
    assert not hasattr(saved_model, "password")


# Teste 4: cpf e photo_url são mapeados do DTO para o UserModel
def test_create_user_maps_cpf_and_photo_url():
    """cpf e photo_url fornecidos no UserCreate devem estar no UserModel salvo."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = None
    hasher.hash.return_value = "hash"
    repo.save.return_value = Mock()

    service = UserService(repo, hasher)
    service.create_user(UserCreate(
        name="João Motorista",
        email="joao@email.com",
        phone="54999999999",
        password="senha123",
        role="driver",
        cpf="999.999.999-99",
        photo_url="https://storage.example.com/avatars/joao.jpg",
    ))

    saved_model = repo.save.call_args[0][0]

    assert saved_model.cpf == "999.999.999-99"
    assert saved_model.photo_url == "https://storage.example.com/avatars/joao.jpg"


# Teste 5: sem cpf — UserModel salvo com cpf=None
def test_create_user_without_cpf_saves_none():
    """Quando cpf não é informado, UserModel deve ser salvo com cpf=None."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = None
    hasher.hash.return_value = "hash"
    repo.save.return_value = Mock()

    service = UserService(repo, hasher)
    service.create_user(UserCreate(
        name="Maria Passageira",
        email="maria@email.com",
        phone="54999999999",
        password="senha123",
        role="passenger",
    ))

    saved_model = repo.save.call_args[0][0]

    assert saved_model.cpf is None
    assert saved_model.photo_url is None


# ===========================================================================
# US02 - TK03: get_user, update_user, delete_user
# ===========================================================================


def make_existing_user(**kwargs):
    defaults = dict(
        id=uuid4(),
        name="John",
        email="john@email.com",
        phone="54999999999",
        password_hash="old_hash",
        role="driver",
    )
    defaults.update(kwargs)
    return UserModel(**defaults)


# --- US02-TK03: implementar get_user, update_user e delete_user em src/domains/users/service.py ---
# Para ativar: remova @pytest.mark.skip dos testes abaixo

# ----- GET USER -----

# Teste 1: get_user retorna o usuário quando encontrado
def test_get_user_success():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    existing_user = make_existing_user()
    repo.find_by_id.return_value = existing_user

    service = UserService(repo, hasher)
    result = service.get_user(user_id)

    repo.find_by_id.assert_called_once_with(user_id)
    assert result == existing_user


# Teste 2: get_user lança UserNotFoundError quando usuário não existe
def test_get_user_not_found():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = None

    service = UserService(repo, hasher)

    with pytest.raises(UserNotFoundError):
        service.get_user(user_id)


# ----- UPDATE USER -----

# Teste 3: update_user com senha chama o hasher e salva o hash
def test_update_user_with_password_hashing():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = make_existing_user()
    hasher.hash.return_value = "new_hashed_password"

    service = UserService(repo, hasher)
    service.update_user(user_id, UserUpdate(password="new_password"))

    hasher.hash.assert_called_once_with("new_password")

    args, _ = repo.update.call_args
    assert args[0] == user_id
    assert args[1]["password_hash"] == "new_hashed_password"


# Teste 4: update_user sem senha não chama o hasher
def test_update_user_without_password():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = make_existing_user()

    service = UserService(repo, hasher)
    service.update_user(user_id, UserUpdate(name="New Name", phone="54888888888"))

    hasher.hash.assert_not_called()

    args, _ = repo.update.call_args
    assert args[0] == user_id
    assert args[1]["name"] == "New Name"
    assert args[1]["phone"] == "54888888888"
    assert "password_hash" not in args[1]


# Teste 5: update_user lança UserNotFoundError e não chama repo.update
def test_update_user_not_found():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = None

    service = UserService(repo, hasher)

    with pytest.raises(UserNotFoundError):
        service.update_user(user_id, UserUpdate(name="New Name"))

    repo.update.assert_not_called()


# ----- DELETE USER -----

# Teste 6: delete_user verifica existência e chama repo.delete
def test_delete_user_success():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = make_existing_user()
    repo.delete.return_value = True

    service = UserService(repo, hasher)
    service.delete_user(user_id)

    repo.find_by_id.assert_called_once_with(user_id)
    repo.delete.assert_called_once_with(user_id)


# Teste 7: delete_user lança UserNotFoundError e não chama repo.delete
def test_delete_user_not_found():
    repo = Mock()
    hasher = Mock()
    user_id = str(uuid4())

    repo.find_by_id.return_value = None

    service = UserService(repo, hasher)

    with pytest.raises(UserNotFoundError):
        service.delete_user(user_id)

    repo.delete.assert_not_called()


# ===========================================================================
# list_users
# ===========================================================================


# Teste 8: list_users retorna todos os usuários do repositório
def test_list_users_returns_all_users():
    """list_users deve delegar para repo.find_all e retornar o resultado."""
    repo = Mock()
    hasher = Mock()

    users = [
        make_existing_user(email="a@email.com"),
        make_existing_user(email="b@email.com"),
    ]
    repo.find_all.return_value = users

    service = UserService(repo, hasher)
    result = service.list_users()

    repo.find_all.assert_called_once()
    assert result == users
    assert len(result) == 2


# Teste 9: list_users com repositório vazio retorna lista vazia
def test_list_users_empty_returns_empty_list():
    """list_users deve retornar lista vazia quando não há usuários."""
    repo = Mock()
    hasher = Mock()

    repo.find_all.return_value = []

    service = UserService(repo, hasher)
    result = service.list_users()

    repo.find_all.assert_called_once()
    assert result == []


# ===========================================================================
# UserService.login (intermediário, sem JWT)
# ===========================================================================


# Teste 1: happy path — email existe, senha confere, retorna o user
def test_login_success():
    """login deve buscar por email, verificar a senha e retornar o UserModel."""
    repo = Mock()
    hasher = Mock()

    existing_user = make_existing_user()
    repo.find_by_email.return_value = existing_user
    hasher.verify.return_value = True

    service = UserService(repo, hasher)
    result = service.login("john@email.com", "senha123")

    repo.find_by_email.assert_called_once_with("john@email.com")
    hasher.verify.assert_called_once_with("senha123", existing_user.password_hash)
    assert result == existing_user


# Teste 2: email não cadastrado lança UserNotFoundError, sem chamar verify
def test_login_user_not_found():
    """login deve lançar UserNotFoundError quando o email não existir."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = None

    service = UserService(repo, hasher)

    with pytest.raises(UserNotFoundError):
        service.login("ghost@email.com", "senha123")

    hasher.verify.assert_not_called()


# Teste 3: senha incorreta lança InvalidCredentialsError
def test_login_invalid_password():
    """login deve lançar InvalidCredentialsError quando a senha não bater."""
    repo = Mock()
    hasher = Mock()

    repo.find_by_email.return_value = make_existing_user()
    hasher.verify.return_value = False

    service = UserService(repo, hasher)

    with pytest.raises(InvalidCredentialsError):
        service.login("john@email.com", "senha_errada")

    hasher.verify.assert_called_once()
