"""US16-TK01 — Regras de senha.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US16-TK01")/d' tests/test_user/test_password_rules.py
"""

import pytest
from pydantic import ValidationError

from src.domains.users.dtos import UserCreate
from src.domains.users.password_rules import WeakPasswordError, validate_password


@pytest.mark.skip(reason="US16-TK01")
def test_strong_password_passes():
    assert validate_password("Senha@123") == "Senha@123"


@pytest.mark.skip(reason="US16-TK01")
def test_min_length_boundary():
    # 8 chars com todas as classes -> válido; 7 chars -> inválido
    assert validate_password("Senha@12") == "Senha@12"
    with pytest.raises(WeakPasswordError):
        validate_password("Senh@12")


@pytest.mark.skip(reason="US16-TK01")
@pytest.mark.parametrize(
    "weak",
    [
        "curta1!",  # < 8
        "semnumero!",  # sem dígito
        "SEM MINUSCULA1!",  # sem minúscula
        "sem maiuscula1!",  # sem maiúscula
        "SemEspecial123",  # sem caractere especial
    ],
)
def test_weak_passwords_rejected(weak):
    with pytest.raises(WeakPasswordError):
        validate_password(weak)


@pytest.mark.skip(reason="US16-TK01")
def test_user_create_rejects_weak_password():
    """A regra precisa estar plugada no cadastro: UserCreate recusa senha fraca."""
    with pytest.raises(ValidationError):
        UserCreate(
            name="John Doe",
            email="john.doe@example.com",
            phone="51999990000",
            password="fraca",
        )


@pytest.mark.skip(reason="US16-TK01")
def test_user_create_accepts_strong_password():
    user = UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="51999990000",
        password="Senha@123",
    )
    assert user.password == "Senha@123"
