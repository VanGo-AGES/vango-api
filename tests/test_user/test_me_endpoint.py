"""US17-TK06 — GET /users/me (perfil do usuário logado).

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK06")/d' tests/test_user/test_me_endpoint.py
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import get_current_user
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def _user():
    now = datetime.now(timezone.utc)
    return UserModel(
        id=uuid4(),
        name="Me User",
        email="me@b.com",
        phone="51999990000",
        role="driver",
        password_hash="h",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.skip(reason="US17-TK06")
def test_me_returns_current_user():
    user = _user()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        resp = client.get("/users/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 200
    assert resp.json()["email"] == "me@b.com"


@pytest.mark.skip(reason="US17-TK06")
def test_me_without_auth_returns_401():
    resp = client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.skip(reason="US17-TK06")
def test_me_integration(db_session):
    from src.config import settings
    from src.infrastructure.auth.jwt_token_service import JwtTokenService
    from src.infrastructure.database import get_db

    user = _user()
    db_session.add(user)
    db_session.flush()
    token = JwtTokenService(
        settings.jwt_secret,
        settings.jwt_algorithm,
        settings.jwt_access_token_expire_minutes,
    ).create_access_token(user.id, role="driver", jti="jti-me")

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json()["email"] == "me@b.com"
