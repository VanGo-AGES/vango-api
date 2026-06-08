"""US17-TK08 — RefreshTokenRepository.

Remova o skip rodando:
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.repositories.refresh_token_repository import RefreshTokenRepositoryImpl
from tests.test_trip._helpers import make_passenger

FUTURE = datetime.now(timezone.utc) + timedelta(days=7)
PAST = datetime.now(timezone.utc) - timedelta(days=1)


def test_create_and_find_valid(db_session):
    user = make_passenger(db_session)
    repo = RefreshTokenRepositoryImpl(db_session)

    created = repo.create(user.id, token_hash="rt-1", expires_at=FUTURE)
    assert created.id is not None

    found = repo.find_valid("rt-1")
    assert found is not None
    assert found.user_id == user.id


def test_find_valid_ignores_expired(db_session):
    user = make_passenger(db_session)
    repo = RefreshTokenRepositoryImpl(db_session)
    repo.create(user.id, token_hash="rt-exp", expires_at=PAST)

    assert repo.find_valid("rt-exp") is None


def test_revoke_invalidates(db_session):
    user = make_passenger(db_session)
    repo = RefreshTokenRepositoryImpl(db_session)
    created = repo.create(user.id, token_hash="rt-2", expires_at=FUTURE)

    repo.revoke(created.id)

    assert repo.find_valid("rt-2") is None


def test_revoke_all_for_user(db_session):
    user = make_passenger(db_session)
    repo = RefreshTokenRepositoryImpl(db_session)
    repo.create(user.id, token_hash="rt-a", expires_at=FUTURE)
    repo.create(user.id, token_hash="rt-b", expires_at=FUTURE)

    count = repo.revoke_all_for_user(user.id)

    assert count == 2
    assert repo.find_valid("rt-a") is None
    assert repo.find_valid("rt-b") is None


def test_find_valid_unknown_returns_none(db_session):
    repo = RefreshTokenRepositoryImpl(db_session)
    assert repo.find_valid("nope") is None
