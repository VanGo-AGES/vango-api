"""US18-TK04 — AuthService.request_password_reset / reset_password.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US18-TK04")/d' tests/test_auth/test_password_reset_service.py
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.users.auth_errors import InvalidResetTokenError
from src.domains.users.auth_service import AuthService


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


@pytest.mark.skip(reason="US18-TK04")
def test_request_reset_existing_user_sends_email():
    repo = Mock()
    repo.find_by_email.return_value = Mock(id=uuid4())
    reset_repo = Mock()
    email = Mock()
    service, _ = _make_service(user_repository=repo, reset_token_repository=reset_repo, email_service=email)

    service.request_password_reset("a@b.com")

    assert reset_repo.create.called
    assert email.send.called


@pytest.mark.skip(reason="US18-TK04")
def test_request_reset_unknown_email_is_neutral():
    repo = Mock()
    repo.find_by_email.return_value = None
    email = Mock()
    service, _ = _make_service(user_repository=repo, email_service=email)

    # não deve levantar nem vazar a inexistência
    service.request_password_reset("missing@b.com")
    assert not email.send.called


@pytest.mark.skip(reason="US18-TK04")
def test_reset_password_valid_token_updates_hash():
    user_id = uuid4()
    reset_repo = Mock()
    token_row = Mock(id=uuid4(), user_id=user_id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1), used_at=None)
    reset_repo.find_valid.return_value = token_row
    user_repo = Mock()
    hasher = Mock()
    hasher.hash.return_value = "new-hash"
    service, _ = _make_service(user_repository=user_repo, password_hasher=hasher, reset_token_repository=reset_repo)

    service.reset_password("raw-token", "Nova@Senha1")

    assert reset_repo.mark_used.called
    assert user_repo.update.called or user_repo.save.called


@pytest.mark.skip(reason="US18-TK04")
def test_reset_password_invalid_token_raises():
    reset_repo = Mock()
    reset_repo.find_valid.return_value = None
    service, _ = _make_service(reset_token_repository=reset_repo)

    with pytest.raises(InvalidResetTokenError):
        service.reset_password("bad-token", "Nova@Senha1")


@pytest.mark.skip(reason="US18-TK04")
def test_reset_password_hashes_the_new_password():
    """A nova senha precisa ser de fato hasheada (não persistida em texto puro)."""
    reset_repo = Mock()
    reset_repo.find_valid.return_value = Mock(
        id=uuid4(),
        user_id=uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used_at=None,
    )
    hasher = Mock()
    hasher.hash.return_value = "hashed-new"
    service, _ = _make_service(password_hasher=hasher, reset_token_repository=reset_repo)

    service.reset_password("raw-token", "Nova@Senha1")

    hasher.hash.assert_called_once_with("Nova@Senha1")


@pytest.mark.skip(reason="US18-TK04")
def test_request_reset_token_belongs_to_user():
    user = Mock(id=uuid4())
    repo = Mock()
    repo.find_by_email.return_value = user
    reset_repo = Mock()
    service, _ = _make_service(user_repository=repo, reset_token_repository=reset_repo, email_service=Mock())

    service.request_password_reset("a@b.com")

    call = reset_repo.create.call_args
    assert user.id in call.args or call.kwargs.get("user_id") == user.id
