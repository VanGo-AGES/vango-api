"""US19-TK03 — Controller POST /auth/logout.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US19-TK03")/d' tests/test_auth/test_logout_controller.py
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domains.users.auth import TokenPayload
from src.infrastructure.auth.dependencies import get_auth_service, get_current_token_payload
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.skip(reason="US19-TK03")
def test_logout_returns_204_and_revokes():
    payload = TokenPayload(sub=uuid4(), role="driver", jti="jti-1", exp=datetime.now(timezone.utc) + timedelta(hours=1))
    calls = {}
    service = type("S", (), {"logout": lambda self, p: calls.setdefault("payload", p)})()

    app.dependency_overrides[get_current_token_payload] = lambda: payload
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/logout", headers={"Authorization": "Bearer x"})
    finally:
        app.dependency_overrides.pop(get_current_token_payload, None)
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 204
    assert calls.get("payload") is payload


@pytest.mark.skip(reason="US19-TK03")
def test_logout_without_auth_returns_401():
    """Sem Bearer token, o logout (rota protegida) deve responder 401."""
    resp = client.post("/auth/logout")
    assert resp.status_code == 401


@pytest.mark.skip(reason="US19-TK03")
def test_logout_integration_persists_revocation(db_session):
    """Stack real: token válido -> 204 -> jti gravado na denylist."""
    from src.config import settings
    from src.domains.users.entity import UserModel
    from src.domains.users.revoked_token_entity import RevokedTokenModel
    from src.infrastructure.auth.jwt_token_service import JwtTokenService
    from src.infrastructure.database import get_db

    now = datetime.now(timezone.utc)
    user = UserModel(
        name="Logout User",
        email="logout@b.com",
        phone="51999990000",
        role="driver",
        password_hash="h",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    token = JwtTokenService(
        settings.jwt_secret,
        settings.jwt_algorithm,
        settings.jwt_access_token_expire_minutes,
    ).create_access_token(user.id, role="driver", jti="jti-int")

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 204
    assert db_session.query(RevokedTokenModel).filter_by(jti="jti-int").count() == 1
