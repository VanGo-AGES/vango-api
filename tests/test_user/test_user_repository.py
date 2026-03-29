import pytest
from uuid import uuid4

from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel
from src.domains.dependents.entity import DependentModel
from src.infrastructure.repositories.user_repository import UserRepositoryImpl


# Teste 1: find user by id — implementado, sem skip
def test_user_repository_find_by_id(db_session):
    repo = UserRepositoryImpl(db_session)

    user = UserModel(
        name="John",
        email="john@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver"
    )

    saved = repo.save(user)

    found = repo.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.email == "john@email.com"

    not_found = repo.find_by_id(uuid4())
    assert not_found is None


# Teste 2: get by email — implementado, sem skip
def test_user_repository_find_by_email(db_session):
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="John",
        email="john@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver"
    ))

    found = repo.find_by_email("john@email.com")
    assert found is not None

    not_found = repo.find_by_email("no@email.com")
    assert not_found is None


# ===========================================================================
# US01 - TK01 (addendum): persistência de cpf e photo_url
# Arquivo: src/infrastructure/repositories/user_repository.py
# ===========================================================================

# Teste 3: motorista salvo com CPF — CPF recuperável do banco
def test_user_repository_save_with_cpf(db_session):
    """CPF informado deve ser persistido e recuperável pelo repositório."""
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="João Motorista",
        email="joao.cpf@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver",
        cpf="999.999.999-99"
    ))

    found = repo.find_by_id(user.id)

    assert found is not None
    assert found.cpf == "999.999.999-99"


# Teste 4: usuário sem CPF — cpf retorna None
def test_user_repository_save_without_cpf(db_session):
    """Usuário criado sem CPF deve ter cpf=None no banco."""
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="Maria Passageira",
        email="maria.nocpf@email.com",
        phone="54999999999",
        password_hash="hash",
        role="passenger"
    ))

    found = repo.find_by_id(user.id)

    assert found is not None
    assert found.cpf is None


# Teste 5: photo_url persistida e recuperável
def test_user_repository_save_with_photo_url(db_session):
    """photo_url informada deve ser persistida e recuperável."""
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="João",
        email="joao.photo@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver",
        photo_url="https://storage.example.com/avatars/joao.jpg"
    ))

    found = repo.find_by_id(user.id)

    assert found is not None
    assert found.photo_url == "https://storage.example.com/avatars/joao.jpg"


# --- US02-TK01: implementar update e delete no UserRepositoryImpl ---
# Para ativar: remova @pytest.mark.skip dos testes abaixo

# Teste 6: update happy path
@pytest.mark.skip(reason="US02-TK01")
def test_user_repository_update(db_session):
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="Old Name",
        email="user@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver"
    ))

    updated = repo.update(user.id, {
        "name": "New Name",
        "phone": "54888888888"
    })

    assert updated.name == "New Name"
    assert updated.phone == "54888888888"

    db_user = repo.find_by_id(user.id)

    assert db_user.name == "New Name"
    assert db_user.phone == "54888888888"


# Teste 7: update usuário inexistente retorna None
@pytest.mark.skip(reason="US02-TK01")
def test_user_repository_update_not_found(db_session):
    repo = UserRepositoryImpl(db_session)

    result = repo.update(uuid4(), {"name": "Test"})

    assert result is None


# Teste 8: delete com cascata (veículo e dependente devem ser removidos)
@pytest.mark.skip(reason="US02-TK01")
def test_user_repository_delete_cascade(db_session):
    repo = UserRepositoryImpl(db_session)

    user = repo.save(UserModel(
        name="John",
        email="john@email.com",
        phone="54999999999",
        password_hash="hash",
        role="driver"
    ))

    # cria dependências com os campos corretos do modelo
    vehicle = VehicleModel(driver_id=user.id, plate="ABC1234", capacity=4)
    dependent = DependentModel(guardian_id=user.id, name="Child")

    db_session.add_all([vehicle, dependent])
    db_session.commit()

    result = repo.delete(user.id)

    assert result is True

    # usuário removido
    assert repo.find_by_id(user.id) is None

    # cascata funcionando
    vehicles = db_session.query(VehicleModel).filter_by(driver_id=user.id).all()
    dependents = db_session.query(DependentModel).filter_by(guardian_id=user.id).all()

    assert vehicles == []
    assert dependents == []


# Teste 9: delete usuário inexistente retorna False
@pytest.mark.skip(reason="US02-TK01")
def test_user_repository_delete_not_found(db_session):
    repo = UserRepositoryImpl(db_session)

    result = repo.delete(uuid4())

    assert result is False
