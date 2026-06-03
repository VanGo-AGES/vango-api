"""US17-TK01 — JwtTokenService.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK01")/d' tests/test_auth/test_jwt_token_service.py
"""

from uuid import uuid4

import pytest

from src.domains.users.auth import TokenPayload
from src.domains.users.auth_errors import InvalidTokenError
from src.infrastructure.auth.jwt_token_service import JwtTokenService

SECRET = "test-secret"


@pytest.mark.skip(reason="US17-TK01")
def test_create_and_decode_round_trip():
    service = JwtTokenService(secret=SECRET)
    user_id = uuid4()

    token = service.create_access_token(user_id, role="driver", jti="jti-1")
    assert isinstance(token, str)

    payload = service.decode_token(token)
    assert isinstance(payload, TokenPayload)
    assert payload.sub == user_id
    assert payload.role == "driver"
    assert payload.jti == "jti-1"


@pytest.mark.skip(reason="US17-TK01")
def test_decode_invalid_token_raises():
    service = JwtTokenService(secret=SECRET)
    with pytest.raises(InvalidTokenError):
        service.decode_token("not-a-jwt")


@pytest.mark.skip(reason="US17-TK01")
def test_decode_with_wrong_secret_raises():
    token = JwtTokenService(secret=SECRET).create_access_token(uuid4(), role="driver")
    with pytest.raises(InvalidTokenError):
        JwtTokenService(secret="other-secret").decode_token(token)


@pytest.mark.skip(reason="US17-TK01")
def test_decode_expired_token_raises():
    # expire_minutes negativo -> token já nasce expirado
    service = JwtTokenService(secret=SECRET, expire_minutes=-1)
    token = service.create_access_token(uuid4(), role="driver")
    with pytest.raises(InvalidTokenError):
        service.decode_token(token)


@pytest.mark.skip(reason="US17-TK01")
def test_token_without_jti_gets_generated_jti_and_exp():
    """Todo token precisa de jti (a denylist do logout/US19 depende disso) e exp."""
    service = JwtTokenService(secret=SECRET)
    token = service.create_access_token(uuid4(), role="driver")  # sem jti explícito

    payload = service.decode_token(token)
    assert payload.jti  # gerado, não vazio
    assert payload.exp is not None
