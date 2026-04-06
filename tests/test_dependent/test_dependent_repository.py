"""
US03 - TK01: Implementar Repositórios de Criação
Arquivo: src/infrastructure/repositories/dependent_repository.py

Testes de persistência para DependentRepositoryImpl.create().
"""

import uuid

import pytest

from src.domains.dependents.entity import DependentModel
from src.domains.users.entity import UserModel
from src.infrastructure.repositories.dependent_repository import DependentRepositoryImpl


def make_guardian(db_session, role: str = "passenger") -> UserModel:
    user = UserModel(
        name="Guardian Test",
        email=f"guardian_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role=role,
    )
    db_session.add(user)
    db_session.flush()
    return user


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_create_dependent_success(db_session):
    """Passageiro cria dependente — retorna objeto persistido com id gerado."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    dependent = DependentModel(guardian_id=guardian.id, name="Ana")
    result = repo.create(dependent)

    assert result.id is not None
    assert result.name == "Ana"
    assert result.guardian_id == guardian.id


def test_create_dependent_persists_in_database(db_session):
    """Dependente criado deve ser recuperável em uma nova query na mesma sessão."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    dependent = DependentModel(guardian_id=guardian.id, name="Pedro")
    repo.create(dependent)

    found = db_session.query(DependentModel).filter_by(name="Pedro").first()
    assert found is not None
    assert found.guardian_id == guardian.id


def test_create_dependent_returns_object_with_generated_id(db_session):
    """ID deve ser gerado automaticamente (uuid4) ao persistir."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    dependent = DependentModel(guardian_id=guardian.id, name="Lucas")
    result = repo.create(dependent)

    assert result.id is not None
    assert isinstance(result.id, uuid.UUID)


# ---------------------------------------------------------------------------
# Associação ao guardião
# ---------------------------------------------------------------------------


def test_create_dependent_associates_correctly_with_guardian(db_session):
    """guardian_id deve corresponder ao UUID do usuário passado."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    dependent = DependentModel(guardian_id=guardian.id, name="Maria")
    result = repo.create(dependent)

    assert result.guardian_id == guardian.id


def test_create_multiple_dependents_same_guardian(db_session):
    """Um guardião pode ter múltiplos dependentes."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    dep1 = DependentModel(guardian_id=guardian.id, name="Filho 1")
    dep2 = DependentModel(guardian_id=guardian.id, name="Filho 2")
    repo.create(dep1)
    repo.create(dep2)

    found = db_session.query(DependentModel).filter_by(guardian_id=guardian.id).all()
    assert len(found) == 2


def test_create_dependent_guardian_role_can_be_guardian(db_session):
    """Usuário com role 'guardian' também pode ser dono de dependentes."""
    guardian = make_guardian(db_session, role="guardian")
    repo = DependentRepositoryImpl(db_session)

    dependent = DependentModel(guardian_id=guardian.id, name="Criança")
    result = repo.create(dependent)

    assert result.guardian_id == guardian.id


# ===========================================================================
# US04 - TK01: Implementar Repositórios de Leitura, Edição e Exclusão
# ===========================================================================


def make_dependent(db_session, guardian, name: str = "Ana") -> DependentModel:
    dependent = DependentModel(guardian_id=guardian.id, name=name)
    db_session.add(dependent)
    db_session.flush()
    return dependent


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


def test_get_dependent_by_id_success(db_session):
    """get_by_id deve retornar o dependente correto quando ele existe."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = make_dependent(db_session, guardian, name="Maria")

    result = repo.get_by_id(dependent.id)

    assert result is not None
    assert result.id == dependent.id
    assert result.name == "Maria"


def test_get_dependent_by_id_not_found(db_session):
    """get_by_id deve retornar None para um UUID inexistente."""
    repo = DependentRepositoryImpl(db_session)

    result = repo.get_by_id(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# get_by_guardian_id
# ---------------------------------------------------------------------------


def test_get_dependents_by_guardian_id_returns_list(db_session):
    """get_by_guardian_id deve retornar todos os dependentes do guardião."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    make_dependent(db_session, guardian, name="Filho 1")
    make_dependent(db_session, guardian, name="Filho 2")

    result = repo.get_by_guardian_id(guardian.id)

    assert len(result) == 2


def test_get_dependents_by_guardian_id_empty(db_session):
    """get_by_guardian_id deve retornar lista vazia quando guardião não tem dependentes."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)

    result = repo.get_by_guardian_id(guardian.id)

    assert result == []


def test_get_dependents_by_guardian_id_only_own(db_session):
    """get_by_guardian_id não deve retornar dependentes de outros guardiões."""
    guardian1 = make_guardian(db_session)
    guardian2 = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    make_dependent(db_session, guardian1, name="G1-Filho")
    make_dependent(db_session, guardian2, name="G2-Filho")

    result = repo.get_by_guardian_id(guardian1.id)

    assert len(result) == 1
    assert result[0].name == "G1-Filho"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_dependent_success(db_session):
    """update deve aplicar o novo nome e retornar o objeto atualizado."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = make_dependent(db_session, guardian, name="Ana")

    result = repo.update(dependent.id, {"name": "Ana Paula"})

    assert result is not None
    assert result.name == "Ana Paula"


def test_update_dependent_not_found(db_session):
    """update deve retornar None quando o dependente não existe."""
    repo = DependentRepositoryImpl(db_session)

    result = repo.update(uuid.uuid4(), {"name": "Novo Nome"})

    assert result is None


def test_update_dependent_persists_in_database(db_session):
    """Alteração feita pelo update deve estar visível em uma nova query."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = make_dependent(db_session, guardian, name="Pedro")

    repo.update(dependent.id, {"name": "Pedro Henrique"})

    found = db_session.query(DependentModel).filter_by(id=dependent.id).first()
    assert found.name == "Pedro Henrique"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_dependent_success(db_session):
    """delete deve retornar True quando o dependente é removido com sucesso."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = make_dependent(db_session, guardian, name="Lucas")

    result = repo.delete(dependent.id)

    assert result is True


def test_delete_dependent_removes_from_database(db_session):
    """Após delete, dependente não deve existir no banco."""
    guardian = make_guardian(db_session)
    repo = DependentRepositoryImpl(db_session)
    dependent = make_dependent(db_session, guardian, name="Julia")

    repo.delete(dependent.id)

    found = db_session.query(DependentModel).filter_by(id=dependent.id).first()
    assert found is None


def test_delete_dependent_not_found(db_session):
    """delete deve retornar False quando o dependente não existe."""
    repo = DependentRepositoryImpl(db_session)

    result = repo.delete(uuid.uuid4())

    assert result is False
