"""
US03 - TK01: Implementar Repositórios de Criação
Arquivo: src/infrastructure/repositories/vehicle_repository.py

Testes de persistência para VehicleRepositoryImpl.create().
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl


def make_driver(db_session) -> UserModel:
    user = UserModel(
        name="Driver Test",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(user)
    db_session.flush()
    return user


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_create_vehicle_success(db_session):
    """Motorista cria veículo com placa e capacidade — retorna objeto persistido."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="ABC1D23", capacity=4)
    result = repo.create(vehicle)

    assert result.id is not None
    assert result.plate == "ABC1D23"
    assert result.capacity == 4
    assert result.driver_id == driver.id


def test_create_vehicle_persists_in_database(db_session):
    """Veículo criado deve ser recuperável em uma nova query na mesma sessão."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="XYZ9W99", capacity=6)
    repo.create(vehicle)

    found = db_session.query(VehicleModel).filter_by(plate="XYZ9W99").first()
    assert found is not None
    assert found.capacity == 6
    assert found.driver_id == driver.id


def test_create_vehicle_returns_object_with_generated_id(db_session):
    """ID deve ser gerado automaticamente (uuid4) ao persistir."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="IDT0001", capacity=4)
    result = repo.create(vehicle)

    assert result.id is not None
    # Deve ser um UUID válido
    assert isinstance(result.id, uuid.UUID)


# ---------------------------------------------------------------------------
# Campo notes (opcional)
# ---------------------------------------------------------------------------


def test_create_vehicle_without_notes(db_session):
    """notes é opcional — criar sem ele não deve lançar exceção."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="NOT0001", capacity=4, notes=None)
    result = repo.create(vehicle)

    assert result.notes is None


def test_create_vehicle_with_notes(db_session):
    """notes preenchido deve ser salvo corretamente."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="NOT0002", capacity=4, notes="Ar condicionado")
    result = repo.create(vehicle)

    assert result.notes == "Ar condicionado"


# ---------------------------------------------------------------------------
# Status padrão
# ---------------------------------------------------------------------------


def test_create_vehicle_default_status_is_active(db_session):
    """status deve ser True por padrão quando não informado."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="STS0001", capacity=4)
    result = repo.create(vehicle)

    assert result.status is True


# ---------------------------------------------------------------------------
# Restrições de banco
# ---------------------------------------------------------------------------


def test_create_vehicle_duplicate_plate_raises_integrity_error(db_session):
    """Placa duplicada deve lançar IntegrityError (constraint unique)."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle1 = VehicleModel(driver_id=driver.id, plate="DUP0001", capacity=4)
    repo.create(vehicle1)

    vehicle2 = VehicleModel(driver_id=driver.id, plate="DUP0001", capacity=6)
    with pytest.raises(IntegrityError):
        repo.create(vehicle2)


def test_create_vehicle_associates_correctly_with_driver(db_session):
    """driver_id deve corresponder ao UUID do motorista passado."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    vehicle = VehicleModel(driver_id=driver.id, plate="ASC0001", capacity=4)
    result = repo.create(vehicle)

    assert result.driver_id == driver.id


# ===========================================================================
# US04 - TK01: Implementar Repositórios de Leitura, Edição e Exclusão
# ===========================================================================


def make_vehicle(db_session, driver, plate: str = "ABC1D23", capacity: int = 4) -> VehicleModel:
    vehicle = VehicleModel(driver_id=driver.id, plate=plate, capacity=capacity)
    db_session.add(vehicle)
    db_session.flush()
    return vehicle


# ---------------------------------------------------------------------------
# get_by_plate
# ---------------------------------------------------------------------------


def test_get_by_plate_found(db_session):
    """get_by_plate deve retornar o veículo quando a placa existe."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    repo.create(VehicleModel(driver_id=driver.id, plate="PLT0001", capacity=4))

    result = repo.get_by_plate("PLT0001")

    assert result is not None
    assert result.plate == "PLT0001"


def test_get_by_plate_not_found(db_session):
    """get_by_plate deve retornar None quando a placa não existe."""
    repo = VehicleRepositoryImpl(db_session)

    result = repo.get_by_plate("INEXISTENTE")

    assert result is None


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


def test_get_vehicle_by_id_success(db_session):
    """get_by_id deve retornar o veículo correto quando ele existe."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="GET0001")

    result = repo.get_by_id(vehicle.id)

    assert result is not None
    assert result.id == vehicle.id
    assert result.plate == "GET0001"


def test_get_vehicle_by_id_not_found(db_session):
    """get_by_id deve retornar None para um UUID inexistente."""
    repo = VehicleRepositoryImpl(db_session)

    result = repo.get_by_id(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# get_by_driver_id
# ---------------------------------------------------------------------------


def test_get_vehicles_by_driver_id_returns_list(db_session):
    """get_by_driver_id deve retornar todos os veículos do motorista."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    make_vehicle(db_session, driver, plate="LST0001")
    make_vehicle(db_session, driver, plate="LST0002")

    result = repo.get_by_driver_id(driver.id)

    assert len(result) == 2


def test_get_vehicles_by_driver_id_empty(db_session):
    """get_by_driver_id deve retornar lista vazia quando motorista não tem veículos."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)

    result = repo.get_by_driver_id(driver.id)

    assert result == []


def test_get_vehicles_by_driver_id_only_own(db_session):
    """get_by_driver_id não deve retornar veículos de outros motoristas."""
    driver1 = make_driver(db_session)
    driver2 = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    make_vehicle(db_session, driver1, plate="OWN0001")
    make_vehicle(db_session, driver2, plate="OWN0002")

    result = repo.get_by_driver_id(driver1.id)

    assert len(result) == 1
    assert result[0].plate == "OWN0001"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_vehicle_success(db_session):
    """update deve aplicar os novos valores e retornar o objeto atualizado."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="UPD0001", capacity=4)

    result = repo.update(vehicle.id, {"plate": "UPD0002", "capacity": 6})

    assert result is not None
    assert result.plate == "UPD0002"
    assert result.capacity == 6


def test_update_vehicle_partial(db_session):
    """update com apenas um campo não deve alterar os demais."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="PTL0001", capacity=4)

    result = repo.update(vehicle.id, {"notes": "Novo adesivo"})

    assert result.notes == "Novo adesivo"
    assert result.plate == "PTL0001"
    assert result.capacity == 4


def test_update_vehicle_not_found(db_session):
    """update deve retornar None quando o veículo não existe."""
    repo = VehicleRepositoryImpl(db_session)

    result = repo.update(uuid.uuid4(), {"plate": "XXX9999"})

    assert result is None


def test_update_vehicle_persists_in_database(db_session):
    """Alteração feita pelo update deve estar visível em uma nova query."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="PRS0001", capacity=4)

    repo.update(vehicle.id, {"capacity": 8})

    found = db_session.query(VehicleModel).filter_by(id=vehicle.id).first()
    assert found.capacity == 8


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_vehicle_success(db_session):
    """delete deve retornar True quando o veículo é removido com sucesso."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="DEL0001")

    result = repo.delete(vehicle.id)

    assert result is True


def test_delete_vehicle_removes_from_database(db_session):
    """Após delete, veículo não deve existir no banco."""
    driver = make_driver(db_session)
    repo = VehicleRepositoryImpl(db_session)
    vehicle = make_vehicle(db_session, driver, plate="DEL0002")

    repo.delete(vehicle.id)

    found = db_session.query(VehicleModel).filter_by(id=vehicle.id).first()
    assert found is None


def test_delete_vehicle_not_found(db_session):
    """delete deve retornar False quando o veículo não existe."""
    repo = VehicleRepositoryImpl(db_session)

    result = repo.delete(uuid.uuid4())

    assert result is False
