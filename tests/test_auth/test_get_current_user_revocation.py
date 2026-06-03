"""US19-TK02 — get_current_token_payload checa a denylist.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US19-TK02")/d' tests/test_auth/test_get_current_user_revocation.py
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.domains.users.auth import TokenPayload
from src.infrastructure.auth.dependencies import get_current_token_payload


@pytest.mark.skip(reason="US19-TK02")
def test_revoked_token_rejected_401():
    token_service = Mock()
    token_service.decode_token.return_value = TokenPayload(
        sub=uuid4(),
        role="driver",
        jti="revoked-jti",
        exp=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    revoked = Mock()
    revoked.is_revoked.return_value = True

    with pytest.raises(HTTPException) as exc:
        get_current_token_payload(
            token_service=token_service,
            revoked_repo=revoked,
            authorization="Bearer revoked.token",
        )
    assert exc.value.status_code == 401
