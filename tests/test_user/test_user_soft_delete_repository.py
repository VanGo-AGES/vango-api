"""US20-TK02 — UserRepository.soft_delete_and_anonymize.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US20-TK02")/d' tests/test_user/test_user_soft_delete_repository.py
"""

import pytest

from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from tests.test_trip._helpers import make_passenger


@pytest.mark.skip(reason="US20-TK02")
def test_soft_delete_marks_inactive_and_anonymizes(db_session):
    user = make_passenger(db_session, name="João Silva")
    user.cpf = "123.456.789-00"
    user.photo_url = "http://x/p.png"
    user.push_token = "fcm-token"
    db_session.flush()
    user_id = user.id
    original_email = user.email

    repo = UserRepositoryImpl(db_session)
    ok = repo.soft_delete_and_anonymize(user_id)
    db_session.flush()

    assert ok is True
    refreshed = db_session.get(type(user), user_id)
    # id preservado para integridade do histórico
    assert refreshed.id == user_id
    # marcado como inativo
    assert refreshed.is_active is False
    assert refreshed.deleted_at is not None
    # PII anonimizada
    assert refreshed.email != original_email
    assert refreshed.name != "João Silva"
    assert refreshed.cpf is None
    assert refreshed.photo_url is None
    assert refreshed.push_token is None


@pytest.mark.skip(reason="US20-TK02")
def test_soft_delete_unknown_user_returns_false(db_session):
    import uuid

    repo = UserRepositoryImpl(db_session)
    assert repo.soft_delete_and_anonymize(uuid.uuid4()) is False
