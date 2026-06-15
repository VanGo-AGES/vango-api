"""US17-TK04 — Controller POST /auth/login.

Remova o skip rodando:
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domains.users.dtos import LoginResponse, UserResponse
from src.domains.users.errors import InvalidCredentialsError
from src.infrastructure.auth.dependencies import get_auth_service
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def _user_response():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return UserResponse(
        id=uuid4(),
        name="John",
        email="john@b.com",
        phone="51999990000",
        role="driver",
        created_at=now,
        updated_at=now,
    )


def test_login_returns_token_200():
    fake = LoginResponse(access_token="jwt.token", token_type="bearer", user=_user_response())
    service = type("S", (), {"login": lambda self, *a, **k: fake})()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/login", json={"email": "john@b.com", "password": "Senha@123"})
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 200
    assert resp.json()["access_token"] == "jwt.token"


def test_login_invalid_credentials_401():
    def _raise(*a, **k):
        raise InvalidCredentialsError()

    service = type("S", (), {"login": lambda self, *a, **k: _raise()})()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/login", json={"email": "john@b.com", "password": "wrong"})
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 401


def test_login_unknown_email_404():
    from src.domains.users.errors import UserNotFoundError

    def _raise(self, *a, **k):
        raise UserNotFoundError()

    service = type("S", (), {"login": _raise})()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.post("/auth/login", json={"email": "nobody@b.com", "password": "Senha@123"})
    finally:
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 404


def test_login_missing_fields_422():
    resp = client.post("/auth/login", json={"email": "john@b.com"})
    assert resp.status_code == 422


def test_login_integration_issues_real_token(db_session):
    """Stack real: usuário semeado no banco -> login emite token de verdade."""
    from datetime import datetime, timezone

    from src.domains.users.entity import UserModel
    from src.infrastructure.database import get_db
    from src.infrastructure.repositories.user_repository import PasswordHasherImpl

    now = datetime.now(timezone.utc)
    user = UserModel(
        name="Login User",
        email="login@b.com",
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
        resp = client.post("/auth/login", json={"email": "login@b.com", "password": "Senha@123"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "login@b.com"
