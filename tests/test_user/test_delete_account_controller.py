"""US20-TK05 — Controller DELETE /users/me.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US20-TK05")/d' tests/test_user/test_delete_account_controller.py
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domains.users.auth_errors import DeletionNotConfirmedError
from src.infrastructure.auth.dependencies import get_auth_service, get_current_user
from src.main import fastapi_app as app

client = TestClient(app, raise_server_exceptions=False)


def _fake_user():
    return type("U", (), {"id": uuid4()})()


def test_delete_my_account_204():
    calls = {}
    service = type("S", (), {"delete_account": lambda self, uid, confirm: calls.update(uid=uid, confirm=confirm)})()
    user = _fake_user()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.request("DELETE", "/users/me", json={"confirm": True})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code == 204
    assert calls["confirm"] is True
    assert calls["uid"] == user.id


def test_delete_my_account_without_confirmation_4xx():
    def _raise(self, uid, confirm):
        raise DeletionNotConfirmedError()

    service = type("S", (), {"delete_account": _raise})()
    app.dependency_overrides[get_current_user] = lambda: _fake_user()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        resp = client.request("DELETE", "/users/me", json={"confirm": False})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_auth_service, None)

    assert resp.status_code in (400, 422)


def test_delete_my_account_without_auth_returns_401():
    """Rota protegida: sem Bearer token, deve responder 401."""
    resp = client.request("DELETE", "/users/me", json={"confirm": True})
    assert resp.status_code == 401


def test_delete_my_account_integration(db_session):
    """Stack real: token válido + confirm -> 204 -> usuário inativo e anonimizado."""
    from datetime import datetime, timezone

    from src.config import settings
    from src.domains.users.entity import UserModel
    from src.infrastructure.auth.jwt_token_service import JwtTokenService
    from src.infrastructure.database import get_db

    now = datetime.now(timezone.utc)
    user = UserModel(
        name="Del User",
        email="del@b.com",
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
    ).create_access_token(user.id, role="driver", jti="jti-del")

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.request(
            "DELETE",
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirm": True},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 204
    refreshed = db_session.get(UserModel, user.id)
    assert refreshed.is_active is False
    assert refreshed.email != "del@b.com"
