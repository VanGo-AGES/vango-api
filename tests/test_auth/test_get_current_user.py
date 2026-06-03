"""US17-TK02 — get_current_user (Bearer JWT).

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK02")/d' tests/test_auth/test_get_current_user.py

Chama as dependências como funções comuns, passando deps mockadas.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.domains.users.auth import TokenPayload
from src.domains.users.auth_errors import InvalidTokenError
from src.infrastructure.auth.dependencies import get_current_token_payload, get_current_user


def _payload(user_id, jti="jti-1"):
    return TokenPayload(sub=user_id, role="driver", jti=jti, exp=datetime.now(timezone.utc) + timedelta(hours=1))


@pytest.mark.skip(reason="US17-TK02")
def test_valid_bearer_returns_payload():
    user_id = uuid4()
    token_service = Mock()
    token_service.decode_token.return_value = _payload(user_id)
    revoked = Mock()
    revoked.is_revoked.return_value = False

    payload = get_current_token_payload(
        token_service=token_service,
        revoked_repo=revoked,
        authorization="Bearer valid.token",
    )
    assert payload.sub == user_id


@pytest.mark.skip(reason="US17-TK02")
def test_missing_authorization_raises_401():
    with pytest.raises(HTTPException) as exc:
        get_current_token_payload(token_service=Mock(), revoked_repo=Mock(), authorization=None)
    assert exc.value.status_code == 401


@pytest.mark.skip(reason="US17-TK02")
def test_invalid_token_raises_401():
    """decode_token falhando (token inválido/expirado) vira 401, não 500."""
    token_service = Mock()
    token_service.decode_token.side_effect = InvalidTokenError()
    with pytest.raises(HTTPException) as exc:
        get_current_token_payload(token_service=token_service, revoked_repo=Mock(), authorization="Bearer bad.token")
    assert exc.value.status_code == 401


@pytest.mark.skip(reason="US17-TK02")
def test_malformed_authorization_scheme_raises_401():
    """Header presente mas sem o esquema 'Bearer ' deve ser rejeitado (401)."""
    with pytest.raises(HTTPException) as exc:
        get_current_token_payload(token_service=Mock(), revoked_repo=Mock(), authorization="Token abc")
    assert exc.value.status_code == 401


@pytest.mark.skip(reason="US17-TK02")
def test_get_current_user_loads_user():
    user_id = uuid4()
    user_repo = Mock()
    user_obj = Mock(id=user_id, is_active=True)
    user_repo.find_by_id.return_value = user_obj

    result = get_current_user(payload=_payload(user_id), user_repo=user_repo)
    assert result is user_obj


@pytest.mark.skip(reason="US17-TK02")
def test_get_current_user_unknown_user_raises_401():
    user_repo = Mock()
    user_repo.find_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_current_user(payload=_payload(uuid4()), user_repo=user_repo)
    assert exc.value.status_code == 401
