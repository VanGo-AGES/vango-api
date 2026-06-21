"""US18-TK05 — Controllers POST /auth/password/forgot e /reset.

Remova o skip rodando:
"""

import pytest
from fastapi.testclient import TestClient

from src.domains.users.auth_errors import InvalidResetTokenError
from src.infrastructure.auth.dependencies import get_auth_service
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def _override(service):
    app.dependency_overrides[get_auth_service] = lambda: service


def _clear():
    app.dependency_overrides.pop(get_auth_service, None)


def test_forgot_password_returns_neutral_200():
    calls = {}
    service = type("S", (), {"request_password_reset": lambda self, email: calls.setdefault("email", email)})()
    _override(service)
    try:
        resp = client.post("/auth/password/forgot", json={"email": "a@b.com"})
    finally:
        _clear()
    assert resp.status_code == 200


def test_reset_password_success_200():
    service = type("S", (), {"reset_password": lambda self, token, new_password: None})()
    _override(service)
    try:
        resp = client.post("/auth/password/reset", json={"token": "tok", "new_password": "Nova@Senha1"})
    finally:
        _clear()
    assert resp.status_code == 200


def test_reset_password_invalid_token_4xx():
    def _raise(self, token, new_password):
        raise InvalidResetTokenError()

    service = type("S", (), {"reset_password": _raise})()
    _override(service)
    try:
        resp = client.post("/auth/password/reset", json={"token": "bad", "new_password": "Nova@Senha1"})
    finally:
        _clear()
    assert resp.status_code in (400, 422)


def test_forgot_password_invalid_email_422():
    resp = client.post("/auth/password/forgot", json={"email": "not-an-email"})
    assert resp.status_code == 422


def test_forgot_password_integration_persists_reset_token(db_session):
    """Stack real (e-mail mockado): forgot de usuário existente cria 1 token de reset."""
    from datetime import datetime, timezone
    from unittest.mock import Mock

    from src.domains.users.entity import UserModel
    from src.domains.users.reset_token_entity import PasswordResetTokenModel
    from src.infrastructure.auth.dependencies import get_email_service
    from src.infrastructure.database import get_db

    now = datetime.now(timezone.utc)
    user = UserModel(
        name="Reset User",
        email="reset@b.com",
        phone="51999990000",
        role="driver",
        password_hash="h",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_email_service] = lambda: Mock()
    try:
        resp = client.post("/auth/password/forgot", json={"email": "reset@b.com"})
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_email_service, None)

    assert resp.status_code == 200
    tokens = db_session.query(PasswordResetTokenModel).filter_by(user_id=user.id).all()
    assert len(tokens) == 1
