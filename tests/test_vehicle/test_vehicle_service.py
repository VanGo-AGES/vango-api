"""
US03 - TK03: Implementar Regras de Negócio de Adição (VehicleService)
Arquivo: src/domains/vehicles/service.py

Testes de lógica de negócio para VehicleService.add_vehicle().
Regra central: apenas usuários com role "driver" podem adicionar veículos.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from src.domains.vehicles.dtos import VehicleCreate
from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.errors import VehicleAccessDeniedError
from src.domains.vehicles.service import VehicleService


def make_mock_repo(plate: str = "ABC1D23", capacity: int = 4) -> MagicMock:
    repo = MagicMock()
    repo.create.return_value = VehicleModel(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        plate=plate,
        capacity=capacity,
    )
    return repo


# ---------------------------------------------------------------------------
# Happy path — role autorizada
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_driver_success():
    """Role 'driver' deve conseguir adicionar veículo sem exceção."""
    repo = make_mock_repo()
    service = VehicleService(repo)

    data = VehicleCreate(plate="ABC1D23", capacity=4)
    result = service.add_vehicle(user_id=str(uuid.uuid4()), user_role="driver", data=data)

    assert result is not None
    repo.create.assert_called_once()


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_calls_repository_with_correct_model(db_session):
    """Service deve montar um VehicleModel com os dados do DTO e passar ao repositório."""
    repo = make_mock_repo(plate="XYZ9W99", capacity=6)
    service = VehicleService(repo)
    user_id = str(uuid.uuid4())

    data = VehicleCreate(plate="XYZ9W99", capacity=6, notes="Ar condicionado")
    service.add_vehicle(user_id=user_id, user_role="driver", data=data)

    call_args = repo.create.call_args[0][0]
    assert call_args.plate == "XYZ9W99"
    assert call_args.capacity == 6
    assert call_args.notes == "Ar condicionado"


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_associates_user_id_to_vehicle(db_session):
    """driver_id no modelo criado deve ser o user_id recebido pelo service."""
    repo = make_mock_repo()
    service = VehicleService(repo)
    user_id = str(uuid.uuid4())

    data = VehicleCreate(plate="ASC0001", capacity=4)
    service.add_vehicle(user_id=user_id, user_role="driver", data=data)

    call_args = repo.create.call_args[0][0]
    assert str(call_args.driver_id) == user_id


# ---------------------------------------------------------------------------
# Roles não autorizadas — deve lançar VehicleAccessDeniedError
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_passenger_forbidden():
    """Role 'passenger' não pode adicionar veículo — deve lançar VehicleAccessDeniedError."""
    repo = make_mock_repo()
    service = VehicleService(repo)

    data = VehicleCreate(plate="ABC1D23", capacity=4)
    with pytest.raises(VehicleAccessDeniedError):
        service.add_vehicle(user_id=str(uuid.uuid4()), user_role="passenger", data=data)


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_guardian_forbidden():
    """Role 'guardian' não pode adicionar veículo — deve lançar VehicleAccessDeniedError."""
    repo = make_mock_repo()
    service = VehicleService(repo)

    data = VehicleCreate(plate="ABC1D23", capacity=4)
    with pytest.raises(VehicleAccessDeniedError):
        service.add_vehicle(user_id=str(uuid.uuid4()), user_role="guardian", data=data)


# ---------------------------------------------------------------------------
# Repositório NÃO deve ser chamado quando role é inválida
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_repository_not_called_when_passenger():
    """Quando role for 'passenger', repositório não deve ser chamado."""
    repo = make_mock_repo()
    service = VehicleService(repo)

    data = VehicleCreate(plate="ABC1D23", capacity=4)
    with pytest.raises(VehicleAccessDeniedError):
        service.add_vehicle(user_id=str(uuid.uuid4()), user_role="passenger", data=data)

    repo.create.assert_not_called()


@pytest.mark.skip(reason="US03-TK03")
def test_add_vehicle_repository_not_called_when_guardian():
    """Quando role for 'guardian', repositório não deve ser chamado."""
    repo = make_mock_repo()
    service = VehicleService(repo)

    data = VehicleCreate(plate="ABC1D23", capacity=4)
    with pytest.raises(VehicleAccessDeniedError):
        service.add_vehicle(user_id=str(uuid.uuid4()), user_role="guardian", data=data)

    repo.create.assert_not_called()


# ===========================================================================
# US04 - TK03: Implementar Regras de Negócio de Edição e Exclusão
# ===========================================================================

from src.domains.vehicles.dtos import VehicleUpdate
from src.domains.vehicles.errors import VehicleNotFoundError, VehicleOwnershipError


def make_owned_vehicle(driver_id: str) -> VehicleModel:
    """Retorna um VehicleModel cujo driver_id é o user_id recebido."""
    return VehicleModel(
        id=uuid.uuid4(),
        driver_id=uuid.UUID(driver_id),
        plate="OWN0001",
        capacity=4,
    )


def make_other_vehicle() -> VehicleModel:
    """Retorna um VehicleModel pertencente a outro driver."""
    return VehicleModel(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        plate="OTHER01",
        capacity=4,
    )


# ---------------------------------------------------------------------------
# get_vehicles
# ---------------------------------------------------------------------------


def test_get_vehicles_returns_list():
    """get_vehicles deve delegar ao repositório e retornar a lista."""
    repo = MagicMock()
    repo.get_by_driver_id.return_value = [
        VehicleModel(id=uuid.uuid4(), driver_id=uuid.uuid4(), plate="L01", capacity=4),
        VehicleModel(id=uuid.uuid4(), driver_id=uuid.uuid4(), plate="L02", capacity=6),
    ]
    service = VehicleService(repo)
    user_id = str(uuid.uuid4())

    result = service.get_vehicles(user_id=user_id)

    assert len(result) == 2
    repo.get_by_driver_id.assert_called_once()


def test_get_vehicles_empty_list():
    """get_vehicles deve retornar lista vazia quando não há veículos."""
    repo = MagicMock()
    repo.get_by_driver_id.return_value = []
    service = VehicleService(repo)

    result = service.get_vehicles(user_id=str(uuid.uuid4()))

    assert result == []


# ---------------------------------------------------------------------------
# get_vehicle (por id com verificação de propriedade)
# ---------------------------------------------------------------------------


def test_get_vehicle_success():
    """get_vehicle deve retornar o veículo quando pertence ao user_id."""
    user_id = str(uuid.uuid4())
    vehicle = make_owned_vehicle(user_id)
    repo = MagicMock()
    repo.get_by_id.return_value = vehicle
    service = VehicleService(repo)

    result = service.get_vehicle(user_id=user_id, vehicle_id=str(vehicle.id))

    assert result is not None


def test_get_vehicle_not_found():
    """get_vehicle deve lançar VehicleNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = VehicleService(repo)

    with pytest.raises(VehicleNotFoundError):
        service.get_vehicle(user_id=str(uuid.uuid4()), vehicle_id=str(uuid.uuid4()))


def test_get_vehicle_wrong_owner():
    """get_vehicle deve lançar VehicleOwnershipError quando o veículo é de outro driver."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_vehicle()
    service = VehicleService(repo)

    with pytest.raises(VehicleOwnershipError):
        service.get_vehicle(user_id=str(uuid.uuid4()), vehicle_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# update_vehicle
# ---------------------------------------------------------------------------


def test_update_vehicle_success():
    """update_vehicle deve chamar repositório e retornar veículo atualizado."""
    user_id = str(uuid.uuid4())
    vehicle = make_owned_vehicle(user_id)
    updated = VehicleModel(id=vehicle.id, driver_id=vehicle.driver_id, plate="NEW0001", capacity=6)
    repo = MagicMock()
    repo.get_by_id.return_value = vehicle
    repo.update.return_value = updated
    service = VehicleService(repo)

    data = VehicleUpdate(plate="NEW0001", capacity=6)
    result = service.update_vehicle(user_id=user_id, vehicle_id=str(vehicle.id), data=data)

    assert result.plate == "NEW0001"
    repo.update.assert_called_once()


def test_update_vehicle_not_found():
    """update_vehicle deve lançar VehicleNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = VehicleService(repo)

    with pytest.raises(VehicleNotFoundError):
        service.update_vehicle(
            user_id=str(uuid.uuid4()),
            vehicle_id=str(uuid.uuid4()),
            data=VehicleUpdate(plate="X"),
        )


def test_update_vehicle_wrong_owner():
    """update_vehicle deve lançar VehicleOwnershipError quando pertence a outro driver."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_vehicle()
    service = VehicleService(repo)

    with pytest.raises(VehicleOwnershipError):
        service.update_vehicle(
            user_id=str(uuid.uuid4()),
            vehicle_id=str(uuid.uuid4()),
            data=VehicleUpdate(plate="X"),
        )


def test_update_vehicle_repo_not_called_when_wrong_owner():
    """Repositório de update não deve ser chamado quando ownership falha."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_vehicle()
    service = VehicleService(repo)

    with pytest.raises(VehicleOwnershipError):
        service.update_vehicle(
            user_id=str(uuid.uuid4()),
            vehicle_id=str(uuid.uuid4()),
            data=VehicleUpdate(capacity=8),
        )

    repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# delete_vehicle
# ---------------------------------------------------------------------------


def test_delete_vehicle_success():
    """delete_vehicle deve chamar repositório sem lançar exceção."""
    user_id = str(uuid.uuid4())
    vehicle = make_owned_vehicle(user_id)
    repo = MagicMock()
    repo.get_by_id.return_value = vehicle
    repo.delete.return_value = True
    service = VehicleService(repo)

    service.delete_vehicle(user_id=user_id, vehicle_id=str(vehicle.id))

    repo.delete.assert_called_once()


def test_delete_vehicle_not_found():
    """delete_vehicle deve lançar VehicleNotFoundError quando ID não existe."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = VehicleService(repo)

    with pytest.raises(VehicleNotFoundError):
        service.delete_vehicle(user_id=str(uuid.uuid4()), vehicle_id=str(uuid.uuid4()))


def test_delete_vehicle_wrong_owner():
    """delete_vehicle deve lançar VehicleOwnershipError quando pertence a outro driver."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_vehicle()
    service = VehicleService(repo)

    with pytest.raises(VehicleOwnershipError):
        service.delete_vehicle(user_id=str(uuid.uuid4()), vehicle_id=str(uuid.uuid4()))


def test_delete_vehicle_repo_not_called_when_wrong_owner():
    """Repositório de delete não deve ser chamado quando ownership falha."""
    repo = MagicMock()
    repo.get_by_id.return_value = make_other_vehicle()
    service = VehicleService(repo)

    with pytest.raises(VehicleOwnershipError):
        service.delete_vehicle(user_id=str(uuid.uuid4()), vehicle_id=str(uuid.uuid4()))

    repo.delete.assert_not_called()
