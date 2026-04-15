"""
US03 - TK03: Implementar Regras de Negócio de Adição (DependentService)
Arquivo: src/domains/dependents/service.py

Testes de lógica de negócio para DependentService.add_dependent().
Regra central: apenas 'passenger' e 'guardian' podem adicionar dependentes.
Role 'driver' deve ser bloqueada com DependentAccessDeniedError.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from src.domains.dependents.dtos import DependentCreate
from src.domains.dependents.entity import DependentModel
from src.domains.dependents.errors import DependentAccessDeniedError
from src.domains.dependents.service import DependentService


def make_mock_repo(name: str = "Ana") -> MagicMock:
    repo = MagicMock()
    repo.create.return_value = DependentModel(
        id=uuid.uuid4(),
        guardian_id=uuid.uuid4(),
        name=name,
    )
    return repo


# ---------------------------------------------------------------------------
# Happy path — roles autorizadas
# ---------------------------------------------------------------------------


def test_add_dependent_passenger_success():
    """Role 'passenger' deve conseguir adicionar dependente."""
    repo = make_mock_repo()
    service = DependentService(repo)

    data = DependentCreate(name="Ana")
    result = service.add_dependent(user_id=str(uuid.uuid4()), user_role="passenger", data=data)

    assert result is not None
    repo.create.assert_called_once()


def test_add_dependent_guardian_success():
    """Role 'guardian' deve conseguir adicionar dependente."""
    repo = make_mock_repo()
    service = DependentService(repo)

    data = DependentCreate(name="Pedro")
    result = service.add_dependent(user_id=str(uuid.uuid4()), user_role="guardian", data=data)

    assert result is not None
    repo.create.assert_called_once()


def test_add_dependent_calls_repository_with_correct_model():
    """Service deve montar um DependentModel com os dados do DTO e passar ao repositório."""
    repo = make_mock_repo(name="João Carlos")
    service = DependentService(repo)
    user_id = str(uuid.uuid4())

    data = DependentCreate(name="João Carlos")
    service.add_dependent(user_id=user_id, user_role="passenger", data=data)

    call_args = repo.create.call_args[0][0]
    assert call_args.name == "João Carlos"


def test_add_dependent_associates_user_id_to_dependent():
    """guardian_id no modelo criado deve ser o user_id recebido pelo service."""
    repo = make_mock_repo()
    service = DependentService(repo)
    user_id = str(uuid.uuid4())

    data = DependentCreate(name="Ana")
    service.add_dependent(user_id=user_id, user_role="passenger", data=data)

    call_args = repo.create.call_args[0][0]
    assert str(call_args.guardian_id) == user_id


# ---------------------------------------------------------------------------
# Role não autorizada — deve lançar DependentAccessDeniedError
# ---------------------------------------------------------------------------


def test_add_dependent_driver_forbidden():
    """Role 'driver' não pode adicionar dependente — deve lançar DependentAccessDeniedError."""
    repo = make_mock_repo()
    service = DependentService(repo)

    data = DependentCreate(name="Ana")
    with pytest.raises(DependentAccessDeniedError):
        service.add_dependent(user_id=str(uuid.uuid4()), user_role="driver", data=data)


# ---------------------------------------------------------------------------
# Repositório NÃO deve ser chamado quando role é inválida
# ---------------------------------------------------------------------------


def test_add_dependent_repository_not_called_when_driver():
    """Quando role for 'driver', repositório não deve ser chamado."""
    repo = make_mock_repo()
    service = DependentService(repo)

    data = DependentCreate(name="Ana")
    with pytest.raises(DependentAccessDeniedError):
        service.add_dependent(user_id=str(uuid.uuid4()), user_role="driver", data=data)

    repo.create.assert_not_called()


# ===========================================================================
# US04 - TK03: Implementar Regras de Negócio de Edição e Exclusão
# ===========================================================================

from src.domains.dependents.dtos import DependentUpdate
from src.domains.dependents.errors import DependentNotFoundError, DependentOwnershipError


def make_owned_dependent(guardian_id: str) -> DependentModel:
    """Retorna um DependentModel cujo guardian_id é o user_id recebido."""
    return DependentModel(
        id=uuid.uuid4(),
        guardian_id=uuid.UUID(guardian_id),
        name="Filho Próprio",
    )


def make_other_dependent() -> DependentModel:
    """Retorna um DependentModel pertencente a outro guardião."""
    return DependentModel(
        id=uuid.uuid4(),
        guardian_id=uuid.uuid4(),
        name="Filho Alheio",
    )


# ---------------------------------------------------------------------------
# get_dependents
# ---------------------------------------------------------------------------


def test_get_dependents_returns_list():
    """get_dependents deve delegar ao repositório e retornar a lista."""
    repo = MagicMock()
    repo.get_by_guardian_id.return_value = [
        DependentModel(id=uuid.uuid4(), guardian_id=uuid.uuid4(), name="Ana"),
        DependentModel(id=uuid.uuid4(), guardian_id=uuid.uuid4(), name="Pedro"),
    ]
    service = DependentService(repo)

    result = service.get_dependents(user_id=str(uuid.uuid4()))

    assert len(result) == 2
    repo.get_by_guardian_id.assert_called_once()


def test_get_dependents_empty_list():
    """get_dependents deve retornar lista vazia quando não há dependentes."""
    repo = MagicMock()
    repo.get_by_guardian_id.return_value = []
    service = DependentService(repo)

    result = service.get_dependents(user_id=str(uuid.uuid4()))

    assert result == []


# ---------------------------------------------------------------------------
# get_dependent (por id com verificação de propriedade)
# ---------------------------------------------------------------------------


def test_get_dependent_success():
    """get_dependent deve retornar o dependente quando pertence ao user_id."""
    user_id = str(uuid.uuid4())
    dependent = make_owned_dependent(user_id)
    repo = MagicMock()
    repo.get_by_id.return_value = dependent
    service = DependentService(repo)

    result = service.get_dependent(user_id=user_id, dependent_id=str(dependent.id))

    assert result is not None


def test_get_dependent_not_found():
    """get_dependent deve lançar DependentNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = DependentService(repo)

    with pytest.raises(DependentNotFoundError):
        service.get_dependent(user_id=str(uuid.uuid4()), dependent_id=str(uuid.uuid4()))


def test_get_dependent_wrong_owner():
    """get_dependent deve lançar DependentOwnershipError quando pertence a outro guardião."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_dependent()
    service = DependentService(repo)

    with pytest.raises(DependentOwnershipError):
        service.get_dependent(user_id=str(uuid.uuid4()), dependent_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# update_dependent
# ---------------------------------------------------------------------------


def test_update_dependent_success():
    """update_dependent deve chamar repositório e retornar dependente atualizado."""
    user_id = str(uuid.uuid4())
    dependent = make_owned_dependent(user_id)
    updated = DependentModel(id=dependent.id, guardian_id=dependent.guardian_id, name="Ana Paula")
    repo = MagicMock()
    repo.get_by_id.return_value = dependent
    repo.update.return_value = updated
    service = DependentService(repo)

    data = DependentUpdate(name="Ana Paula")
    result = service.update_dependent(user_id=user_id, dependent_id=str(dependent.id), data=data)

    assert result.name == "Ana Paula"
    repo.update.assert_called_once()


def test_update_dependent_not_found():
    """update_dependent deve lançar DependentNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = DependentService(repo)

    with pytest.raises(DependentNotFoundError):
        service.update_dependent(
            user_id=str(uuid.uuid4()),
            dependent_id=str(uuid.uuid4()),
            data=DependentUpdate(name="X"),
        )


def test_update_dependent_wrong_owner():
    """update_dependent deve lançar DependentOwnershipError quando pertence a outro guardião."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_dependent()
    service = DependentService(repo)

    with pytest.raises(DependentOwnershipError):
        service.update_dependent(
            user_id=str(uuid.uuid4()),
            dependent_id=str(uuid.uuid4()),
            data=DependentUpdate(name="X"),
        )


def test_update_dependent_repo_not_called_when_wrong_owner():
    """Repositório de update não deve ser chamado quando ownership falha."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_dependent()
    service = DependentService(repo)

    with pytest.raises(DependentOwnershipError):
        service.update_dependent(
            user_id=str(uuid.uuid4()),
            dependent_id=str(uuid.uuid4()),
            data=DependentUpdate(name="X"),
        )

    repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# delete_dependent
# ---------------------------------------------------------------------------


def test_delete_dependent_success():
    """delete_dependent deve chamar repositório sem lançar exceção."""
    user_id = str(uuid.uuid4())
    dependent = make_owned_dependent(user_id)
    repo = MagicMock()
    repo.get_by_id.return_value = dependent
    repo.delete.return_value = True
    service = DependentService(repo)

    service.delete_dependent(user_id=user_id, dependent_id=str(dependent.id))

    repo.delete.assert_called_once()


def test_delete_dependent_not_found():
    """delete_dependent deve lançar DependentNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = DependentService(repo)

    with pytest.raises(DependentNotFoundError):
        service.delete_dependent(user_id=str(uuid.uuid4()), dependent_id=str(uuid.uuid4()))


def test_delete_dependent_wrong_owner():
    """delete_dependent deve lançar DependentOwnershipError quando pertence a outro guardião."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_dependent()
    service = DependentService(repo)

    with pytest.raises(DependentOwnershipError):
        service.delete_dependent(user_id=str(uuid.uuid4()), dependent_id=str(uuid.uuid4()))


def test_delete_dependent_repo_not_called_when_wrong_owner():
    """Repositório de delete não deve ser chamado quando ownership falha."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_dependent()
    service = DependentService(repo)

    with pytest.raises(DependentOwnershipError):
        service.delete_dependent(user_id=str(uuid.uuid4()), dependent_id=str(uuid.uuid4()))

    repo.delete.assert_not_called()
