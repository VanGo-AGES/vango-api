"""US19-TK02 — AuthService.logout.

Remova o skip rodando:
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.users.auth import TokenPayload
from src.domains.users.auth_service import AuthService


def _make_service(revoked_repo):
    return AuthService(
        user_repository=Mock(),
        password_hasher=Mock(),
        token_service=Mock(),
        reset_token_repository=Mock(),
        email_service=Mock(),
        revoked_token_repository=revoked_repo,
    )


def test_logout_revokes_current_jti():
    revoked = Mock()
    service = _make_service(revoked)
    payload = TokenPayload(
        sub=uuid4(),
        role="driver",
        jti="jti-xyz",
        exp=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    service.logout(payload)

    assert revoked.revoke.called
    called_jti = revoked.revoke.call_args.args[0] if revoked.revoke.call_args.args else revoked.revoke.call_args.kwargs.get("jti")
    assert called_jti == "jti-xyz"


def test_logout_revokes_with_user_and_expiry():
    """A entrada da denylist precisa carregar user_id e o exp do token (housekeeping)."""
    revoked = Mock()
    service = _make_service(revoked)
    user_id = uuid4()
    exp = datetime.now(timezone.utc) + timedelta(hours=2)
    payload = TokenPayload(sub=user_id, role="driver", jti="jti-abc", exp=exp)

    service.logout(payload)

    call = revoked.revoke.call_args
    passed = list(call.args) + list(call.kwargs.values())
    assert "jti-abc" in passed
    assert user_id in passed
    assert exp in passed
