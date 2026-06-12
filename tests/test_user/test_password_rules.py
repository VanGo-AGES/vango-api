"""US16-TK01 — Regras de senha."""

import pytest
from pydantic import ValidationError

from src.domains.users.dtos import UserCreate, UserUpdate
from src.domains.users.password_rules import WeakPasswordError, validate_password

# Senhas que violam exatamente uma das regras de `validate_password`.
WEAK_PASSWORDS = [
    "curta1!",  # < 8
    "semnumero!",  # sem dígito
    "SEM MINUSCULA1!",  # sem minúscula
    "sem maiuscula1!",  # sem maiúscula
    "SemEspecial123",  # sem caractere especial
]


def test_strong_password_passes():
    assert validate_password("Senha@123") == "Senha@123"


def test_min_length_boundary():
    # 8 chars com todas as classes -> válido; 7 chars -> inválido
    assert validate_password("Senha@12") == "Senha@12"
    with pytest.raises(WeakPasswordError):
        validate_password("Senh@12")


@pytest.mark.parametrize("weak", WEAK_PASSWORDS)
def test_weak_passwords_rejected(weak):
    with pytest.raises(WeakPasswordError):
        validate_password(weak)


def test_user_create_rejects_weak_password():
    """A regra precisa estar plugada no cadastro: UserCreate recusa senha fraca."""
    with pytest.raises(ValidationError):
        UserCreate(
            name="John Doe",
            email="john.doe@example.com",
            phone="51999990000",
            password="fraca",
        )


def test_user_create_accepts_strong_password():
    user = UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="51999990000",
        password="Senha@123",
    )
    assert user.password == "Senha@123"


# A mesma política precisa valer na troca de senha (UserUpdate).
@pytest.mark.parametrize("weak", WEAK_PASSWORDS)
def test_user_update_rejects_weak_password(weak):
    with pytest.raises(ValidationError):
        UserUpdate(password=weak)


def test_user_update_accepts_strong_password_boundary():
    # exatamente 8 chars com todas as classes -> válido
    user = UserUpdate(password="Senha@12")
    assert user.password == "Senha@12"


def test_user_update_password_optional_none_allowed():
    """password é opcional no UserUpdate: None não dispara validação de força."""
    user = UserUpdate(name="John Doe")
    assert user.password is None
