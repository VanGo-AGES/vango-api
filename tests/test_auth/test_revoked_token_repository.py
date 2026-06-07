"""US19-TK01 — RevokedTokenRepository (denylist por jti).

Remova o skip rodando:
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.repositories.revoked_token_repository import RevokedTokenRepositoryImpl
from tests.test_trip._helpers import make_passenger

FUTURE = datetime.now(timezone.utc) + timedelta(hours=1)


def test_revoke_then_is_revoked_true(db_session):
    user = make_passenger(db_session)
    repo = RevokedTokenRepositoryImpl(db_session)

    repo.revoke("jti-1", user.id, FUTURE)

    assert repo.is_revoked("jti-1") is True


def test_unknown_jti_is_not_revoked(db_session):
    repo = RevokedTokenRepositoryImpl(db_session)
    assert repo.is_revoked("never-seen") is False


def test_revoke_is_idempotent(db_session):
    """jti é PK: revogar o mesmo jti duas vezes (logout duplo) não pode estourar."""
    user = make_passenger(db_session)
    repo = RevokedTokenRepositoryImpl(db_session)

    repo.revoke("jti-dup", user.id, FUTURE)
    repo.revoke("jti-dup", user.id, FUTURE)

    assert repo.is_revoked("jti-dup") is True
