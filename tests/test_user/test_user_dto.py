import pytest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from src.domains.users.dtos import UserCreate, UserResponse, UserUpdate


# ----- USER CREATE — implementado, sem skip -----

def test_user_create_empty_fields():
    # name vazio (min_length=3)
    with pytest.raises(ValidationError):
        UserCreate(
            name="",
            email="test@email.com",
            phone="54999999999",
            password="123456",
            role="driver"
        )

    # email omitido
    with pytest.raises(ValidationError):
        UserCreate(
            name="John Doe",
            phone="54999999999",
            password="123456",
            role="driver"
        )


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            name="John Doe",
            email="email_sem_arroba",
            phone="54999999999",
            password="123456",
            role="driver"
        )


def test_user_create_invalid_role():
    with pytest.raises(ValidationError):
        UserCreate(
            name="John Doe",
            email="john@email.com",
            phone="54999999999",
            password="123456",
            role="admin"
        )


def test_user_response_no_password_exposure():
    user = UserResponse(
        id=uuid4(),
        name="John Doe",
        email="john@email.com",
        phone="54999999999",
        role="driver",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    data = user.model_dump()

    assert "password_hash" not in data
    assert "password" not in data


def test_user_create_valid():
    user = UserCreate(
        name="John Doe",
        email="john@email.com",
        phone="54999999999",
        password="123456",
        role="driver"
    )

    assert user.name == "John Doe"


# ===========================================================================
# US01 - TK02 (addendum): cpf e photo_url nos contratos de usuário
# Arquivo: src/domains/users/dtos.py
# ===========================================================================

# Teste 6: motorista informa CPF no cadastro
def test_user_create_driver_with_cpf():
    """Motorista pode incluir CPF no momento do cadastro."""
    user = UserCreate(
        name="João Motorista",
        email="joao@email.com",
        phone="54999999999",
        password="123456",
        role="driver",
        cpf="999.999.999-99"
    )

    assert user.cpf == "999.999.999-99"


# Teste 7: CPF é opcional — passageiro não precisa informar
def test_user_create_without_cpf():
    """CPF é opcional — omitir não deve causar ValidationError."""
    user = UserCreate(
        name="Maria Passageira",
        email="maria@email.com",
        phone="54999999999",
        password="123456",
        role="passenger"
    )

    assert user.cpf is None


# Teste 8: UserResponse expõe cpf e photo_url
def test_user_response_exposes_cpf_and_photo_url():
    """UserResponse deve incluir os campos cpf e photo_url quando preenchidos."""
    user = UserResponse(
        id=uuid4(),
        name="João Silva",
        email="joao@email.com",
        phone="54999999999",
        role="driver",
        cpf="999.999.999-99",
        photo_url="https://storage.example.com/avatars/joao.jpg",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    assert user.cpf == "999.999.999-99"
    assert user.photo_url == "https://storage.example.com/avatars/joao.jpg"


# Teste 9: cpf e photo_url podem ser None em UserResponse
def test_user_response_cpf_and_photo_url_nullable():
    """cpf e photo_url devem aceitar None (campos opcionais)."""
    user = UserResponse(
        id=uuid4(),
        name="Maria",
        email="maria@email.com",
        phone="54999999999",
        role="passenger",
        cpf=None,
        photo_url=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    assert user.cpf is None
    assert user.photo_url is None


# Teste 10: UserUpdate aceita cpf e photo_url como campos opcionais
def test_user_update_cpf_and_photo_url():
    """Perfil pode ser atualizado informando cpf e/ou photo_url."""
    update = UserUpdate(
        cpf="999.999.999-99",
        photo_url="https://storage.example.com/avatars/novo.jpg"
    )

    data = update.model_dump(exclude_unset=True)

    assert data["cpf"] == "999.999.999-99"
    assert data["photo_url"] == "https://storage.example.com/avatars/novo.jpg"


# --- US02-TK02: implementar validações no UserUpdate em src/domains/users/dtos.py ---
# Para ativar: remova @pytest.mark.skip dos testes abaixo

# Teste 1: campos opcionais — update parcial com apenas um campo
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_partial_success():
    user = UserUpdate(phone="54999999999")

    data = user.model_dump(exclude_unset=True)

    assert data == {"phone": "54999999999"}


# Teste 2: password vazio rejeitado
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_empty_password():
    with pytest.raises(ValidationError):
        UserUpdate(password="")


# Teste 3: happy path — todos os campos válidos
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_happy_path():
    user = UserUpdate(
        name="John Updated",
        email="john.updated@email.com",
        phone="54988888888",
        password="nova_senha_123"
    )

    data = user.model_dump(exclude_unset=True)

    assert data["name"] == "John Updated"
    assert data["email"] == "john.updated@email.com"
    assert data["phone"] == "54988888888"
    assert data["password"] == "nova_senha_123"


# Teste 4: email normalizado (lowercase + strip)
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_email_normalization():
    user = UserUpdate(email="  JOHN.DOE@EMAIL.COM  ")

    data = user.model_dump(exclude_unset=True)

    assert data["email"] == "john.doe@email.com"


# Teste 5: formato de email inválido rejeitado
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_invalid_email():
    with pytest.raises(ValidationError):
        UserUpdate(email="email_invalido")


# Teste 6: name vazio rejeitado
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_empty_name():
    with pytest.raises(ValidationError):
        UserUpdate(name="")


# Teste 7: phone vazio rejeitado
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_empty_phone():
    with pytest.raises(ValidationError):
        UserUpdate(phone="")


# Teste 8: update sem nenhum campo é válido (noop)
@pytest.mark.skip(reason="US02-TK02")
def test_user_update_no_fields_is_valid():
    user = UserUpdate()

    data = user.model_dump(exclude_unset=True)

    assert data == {}
