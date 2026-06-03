"""US20-TK04 — AuthService.delete_account.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US20-TK04")/d' tests/test_user/test_delete_account_service.py
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.users.auth_errors import DeletionNotConfirmedError
from src.domains.users.auth_service import AuthService
from src.domains.users.errors import UserNotFoundError


def _make_service(user_repo):
    return AuthService(
        user_repository=user_repo,
        password_hasher=Mock(),
        token_service=Mock(),
        reset_token_repository=Mock(),
        email_service=Mock(),
        revoked_token_repository=Mock(),
    )


@pytest.mark.skip(reason="US20-TK04")
def test_delete_account_confirmed_soft_deletes():
    user_repo = Mock()
    user_repo.soft_delete_and_anonymize.return_value = True
    service = _make_service(user_repo)

    service.delete_account(uuid4(), confirm=True)

    assert user_repo.soft_delete_and_anonymize.called


@pytest.mark.skip(reason="US20-TK04")
def test_delete_account_not_confirmed_raises():
    user_repo = Mock()
    service = _make_service(user_repo)

    with pytest.raises(DeletionNotConfirmedError):
        service.delete_account(uuid4(), confirm=False)

    assert not user_repo.soft_delete_and_anonymize.called


@pytest.mark.skip(reason="US20-TK04")
def test_delete_account_unknown_user_raises():
    user_repo = Mock()
    user_repo.soft_delete_and_anonymize.return_value = False
    service = _make_service(user_repo)

    with pytest.raises(UserNotFoundError):
        service.delete_account(uuid4(), confirm=True)
