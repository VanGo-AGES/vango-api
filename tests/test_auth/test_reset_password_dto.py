"""US18-TK03 — DTOs de recuperação de senha.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US18-TK03")/d' tests/test_auth/test_reset_password_dto.py
"""

import pytest
from pydantic import ValidationError

from src.domains.users.dtos import ForgotPasswordRequest, ResetPasswordConfirm


@pytest.mark.skip(reason="US18-TK03")
def test_forgot_password_requires_valid_email():
    assert ForgotPasswordRequest(email="a@b.com").email == "a@b.com"
    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="not-an-email")


@pytest.mark.skip(reason="US18-TK03")
def test_reset_password_confirm_fields():
    dto = ResetPasswordConfirm(token="tok-123", new_password="Senha@123")
    assert dto.token == "tok-123"
    assert dto.new_password == "Senha@123"


@pytest.mark.skip(reason="US18-TK03")
def test_reset_password_confirm_requires_token():
    with pytest.raises(ValidationError):
        ResetPasswordConfirm(token="", new_password="Senha@123")


@pytest.mark.skip(reason="US18-TK03")
def test_reset_password_confirm_rejects_weak_new_password():
    """A nova senha no reset precisa respeitar as mesmas regras do cadastro (US16-TK01)."""
    with pytest.raises(ValidationError):
        ResetPasswordConfirm(token="tok-123", new_password="fraca")
