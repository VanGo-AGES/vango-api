"""US17-TK10 — Controller POST /auth/refresh.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK10")/d' tests/test_auth/test_refresh_controller.py
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domains.users.auth_errors import InvalidRefreshTokenError
from src.domains.users.dtos import LoginResponse, UserResponse
from src.infrastructure.auth.dependencies import get_auth_service
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def _user_response():
    now = datetime.now(timezone.utc)
    return UserResponse(
        id=uuid4(),
        name="R",
        email="r@b.com",
        phone="51999990000",
        role="driver",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.skip(reason="US17-TK10")
def test_refresh_returns_new_tokens():
    fake = LoginResponse(access_token="a2", token_type="bearer", user=_user_response(), refresh_token="r2")
    service = type("S", (), {"refresh": lambda self, t: fake})()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/refresh", json={"refresh_token": "r1"})
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "a2"
    assert body["refresh_token"] == "r2"


@pytest.mark.skip(reason="US17-TK10")
def test_refresh_invalid_returns_401():
    def _raise(self, t):
        raise InvalidRefreshTokenError()

    service = type("S", (), {"refresh": _raise})()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/refresh", json={"refresh_token": "bad"})
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 401


@pytest.mark.skip(reason="US17-TK10")
def test_refresh_integration_login_then_rotate(db_session):
    """Stack real: login -> refresh rotaciona -> reusar o refresh antigo falha."""
    from src.domains.users.entity import UserModel
    from src.infrastructure.database import get_db
    from src.infrastructure.repositories.user_repository import PasswordHasherImpl

    now = datetime.now(timezone.utc)
    user = UserModel(
        name="Rot User",
        email="rot@b.com",
        phone="51999990000",
        role="driver",
        password_hash=PasswordHasherImpl().hash("Senha@123"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        login = client.post("/auth/login", json={"email": "rot@b.com", "password": "Senha@123"})
        old_refresh = login.json()["refresh_token"]

        first = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        reuse = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert first.status_code == 200
    assert first.json()["access_token"]
    # rotação: o refresh antigo foi revogado, reusá-lo falha
    assert reuse.status_code == 401
