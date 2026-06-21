"""US17-TK09 — AuthService: login emite refresh + refresh() com rotação.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK09")/d' tests/test_auth/test_refresh_service.py
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.users.auth_errors import InvalidRefreshTokenError
from src.domains.users.auth_service import AuthService
from src.domains.users.dtos import LoginResponse
from src.domains.users.entity import UserModel


def _make_service(**overrides):
    deps = dict(
        user_repository=Mock(),
        password_hasher=Mock(),
        token_service=Mock(),
        reset_token_repository=Mock(),
        email_service=Mock(),
        revoked_token_repository=Mock(),
        refresh_token_repository=Mock(),
    )
    deps.update(overrides)
    return AuthService(**deps), deps


def _user():
    now = datetime.now(timezone.utc)
    return UserModel(
        id=uuid4(),
        name="R",
        email="r@b.com",
        phone="51999990000",
        role="driver",
        password_hash="h",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def test_login_issues_refresh_token():
    user = _user()
    repo = Mock()
    repo.find_by_email.return_value = user
    hasher = Mock()
    hasher.verify.return_value = True
    tokens = Mock()
    tokens.create_access_token.return_value = "access.jwt"
    refresh_repo = Mock()

    service, _ = _make_service(
        user_repository=repo,
        password_hasher=hasher,
        token_service=tokens,
        refresh_token_repository=refresh_repo,
    )
    result = service.login("r@b.com", "Senha@123")

    assert isinstance(result, LoginResponse)
    assert result.refresh_token  # refresh emitido
    assert refresh_repo.create.called  # hash do refresh persistido


def test_refresh_rotates_and_revokes_old():
    user = _user()
    refresh_repo = Mock()
    refresh_repo.find_valid.return_value = Mock(id=uuid4(), user_id=user.id)
    user_repo = Mock()
    user_repo.find_by_id.return_value = user
    tokens = Mock()
    tokens.create_access_token.return_value = "new.access"

    service, _ = _make_service(user_repository=user_repo, token_service=tokens, refresh_token_repository=refresh_repo)
    result = service.refresh("raw-refresh")

    assert result.access_token == "new.access"
    assert result.refresh_token  # novo refresh emitido
    assert refresh_repo.revoke.called  # o refresh usado é revogado (rotação)
    assert refresh_repo.create.called  # novo refresh persistido


def test_refresh_invalid_raises():
    refresh_repo = Mock()
    refresh_repo.find_valid.return_value = None
    service, _ = _make_service(refresh_token_repository=refresh_repo)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh("bad-or-revoked")
