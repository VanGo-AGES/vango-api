"""US20-TK03 — Finders excluem usuários inativos.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US20-TK03")/d' tests/test_user/test_user_finders_active.py
"""

import pytest

from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from tests.test_trip._helpers import make_passenger


def _deactivate(db_session, user):
    user.is_active = False
    db_session.flush()


@pytest.mark.skip(reason="US20-TK03")
def test_active_user_is_still_found(db_session):
    """Controle positivo: o filtro não pode esconder usuários ativos."""
    user = make_passenger(db_session)
    db_session.flush()

    repo = UserRepositoryImpl(db_session)
    assert repo.find_by_email(user.email) is not None
    assert repo.find_by_id(user.id) is not None


@pytest.mark.skip(reason="US20-TK03")
def test_find_by_email_excludes_inactive(db_session):
    user = make_passenger(db_session)
    email = user.email
    _deactivate(db_session, user)

    repo = UserRepositoryImpl(db_session)
    assert repo.find_by_email(email) is None


@pytest.mark.skip(reason="US20-TK03")
def test_find_by_id_excludes_inactive(db_session):
    user = make_passenger(db_session)
    _deactivate(db_session, user)

    repo = UserRepositoryImpl(db_session)
    assert repo.find_by_id(user.id) is None


@pytest.mark.skip(reason="US20-TK03")
def test_find_all_excludes_inactive(db_session):
    active = make_passenger(db_session)
    inactive = make_passenger(db_session)
    _deactivate(db_session, inactive)

    repo = UserRepositoryImpl(db_session)
    ids = {u.id for u in repo.find_all()}
    assert active.id in ids
    assert inactive.id not in ids
