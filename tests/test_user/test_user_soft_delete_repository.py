"""US20-TK02 — UserRepository.soft_delete_and_anonymize.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US20-TK02")/d' tests/test_user/test_user_soft_delete_repository.py
"""

import pytest

from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from tests.test_trip._helpers import make_driver, make_passenger, make_route


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


@pytest.mark.skip(reason="US20-TK02")
def test_soft_delete_keeps_email_unique_across_users(db_session):
    """O e-mail anonimizado precisa continuar único (coluna unique): dois
    usuários deletados não podem colidir."""
    u1 = make_passenger(db_session)
    u2 = make_passenger(db_session)
    db_session.flush()

    repo = UserRepositoryImpl(db_session)
    assert repo.soft_delete_and_anonymize(u1.id) is True
    assert repo.soft_delete_and_anonymize(u2.id) is True
    db_session.flush()  # não pode violar a unique constraint de email

    r1 = db_session.get(type(u1), u1.id)
    r2 = db_session.get(type(u2), u2.id)
    assert r1.email != r2.email


@pytest.mark.skip(reason="US20-TK02")
def test_soft_delete_preserves_history(db_session):
    """Soft delete NÃO cascateia: o histórico (rotas/viagens) do usuário
    continua no banco — diferente do hard delete."""
    from src.domains.routes.entity import RouteModel

    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    db_session.flush()

    repo = UserRepositoryImpl(db_session)
    assert repo.soft_delete_and_anonymize(driver.id) is True
    db_session.flush()

    # a rota (histórico) sobrevive e o usuário continua na tabela (só inativo)
    assert db_session.get(RouteModel, route.id) is not None
    assert db_session.get(type(driver), driver.id) is not None
