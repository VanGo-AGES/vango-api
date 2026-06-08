"""US18-TK02 — PasswordResetTokenRepository.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US18-TK02")/d' tests/test_auth/test_password_reset_token_repository.py
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.repositories.password_reset_token_repository import PasswordResetTokenRepositoryImpl
from tests.test_trip._helpers import make_passenger

FUTURE = datetime.now(timezone.utc) + timedelta(hours=1)
PAST = datetime.now(timezone.utc) - timedelta(hours=1)


def test_create_and_find_valid(db_session):
    user = make_passenger(db_session)
    repo = PasswordResetTokenRepositoryImpl(db_session)

    created = repo.create(user.id, token_hash="hash-1", expires_at=FUTURE)
    assert created.id is not None

    found = repo.find_valid("hash-1")
    assert found is not None
    assert found.user_id == user.id


def test_find_valid_ignores_expired(db_session):
    user = make_passenger(db_session)
    repo = PasswordResetTokenRepositoryImpl(db_session)
    repo.create(user.id, token_hash="expired", expires_at=PAST)

    assert repo.find_valid("expired") is None


def test_mark_used_invalidates_token(db_session):
    user = make_passenger(db_session)
    repo = PasswordResetTokenRepositoryImpl(db_session)
    created = repo.create(user.id, token_hash="hash-2", expires_at=FUTURE)

    repo.mark_used(created.id)

    assert repo.find_valid("hash-2") is None


def test_find_valid_unknown_returns_none(db_session):
    repo = PasswordResetTokenRepositoryImpl(db_session)
    assert repo.find_valid("nope") is None


def test_mark_used_unknown_id_is_noop(db_session):
    """mark_used em id inexistente (ex.: duplo-reset concorrente) não pode estourar."""
    import uuid

    repo = PasswordResetTokenRepositoryImpl(db_session)
    repo.mark_used(uuid.uuid4())  # não deve levantar
