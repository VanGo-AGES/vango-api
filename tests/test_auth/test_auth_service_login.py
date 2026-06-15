"""US17-TK03 — AuthService.login.

Remova o skip rodando:
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.users.auth_errors import AccountInactiveError
from src.domains.users.auth_service import AuthService
from src.domains.users.dtos import LoginResponse
from src.domains.users.entity import UserModel
from src.domains.users.errors import InvalidCredentialsError, UserNotFoundError


def _make_service(**overrides):
    deps = dict(
        user_repository=Mock(),
        password_hasher=Mock(),
        token_service=Mock(),
        reset_token_repository=Mock(),
        email_service=Mock(),
        revoked_token_repository=Mock(),
    )
    deps.update(overrides)
    return AuthService(**deps), deps


def _make_user(**kw):
    """UserModel completo (sem DB) — tem os campos que o UserResponse exige."""
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        name="John Doe",
        email="john@b.com",
        phone="51999990000",
        role="driver",
        password_hash="h",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    defaults.update(kw)
    return UserModel(**defaults)


def test_login_success_returns_token():
    user = _make_user()
    repo = Mock()
    repo.find_by_email.return_value = user
    hasher = Mock()
    hasher.verify.return_value = True
    tokens = Mock()
    tokens.create_access_token.return_value = "jwt.token.here"

    service, _ = _make_service(user_repository=repo, password_hasher=hasher, token_service=tokens)
    result = service.login("john@b.com", "Senha@123")

    assert isinstance(result, LoginResponse)
    assert result.access_token == "jwt.token.here"
    assert result.token_type == "bearer"
    # o LoginResponse reflete quem logou
    assert result.user.email == user.email
    # o token é emitido para o usuário certo (sub + role)
    call = tokens.create_access_token.call_args
    assert user.id in call.args or call.kwargs.get("user_id") == user.id
    assert user.role in call.args or call.kwargs.get("role") == user.role


def test_login_unknown_email_raises():
    repo = Mock()
    repo.find_by_email.return_value = None
    service, _ = _make_service(user_repository=repo)
    with pytest.raises(UserNotFoundError):
        service.login("missing@b.com", "x")


def test_login_wrong_password_raises():
    repo = Mock()
    repo.find_by_email.return_value = Mock(is_active=True, password_hash="h")
    hasher = Mock()
    hasher.verify.return_value = False
    service, _ = _make_service(user_repository=repo, password_hasher=hasher)
    with pytest.raises(InvalidCredentialsError):
        service.login("a@b.com", "wrong")


def test_login_inactive_account_blocked():
    repo = Mock()
    repo.find_by_email.return_value = Mock(is_active=False, password_hash="h")
    hasher = Mock()
    hasher.verify.return_value = True
    service, _ = _make_service(user_repository=repo, password_hasher=hasher)
    with pytest.raises((AccountInactiveError, InvalidCredentialsError, UserNotFoundError)):
        service.login("a@b.com", "Senha@123")
