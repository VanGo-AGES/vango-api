"""
US03 - TK02: Implementar Contratos de Criação (Schema de Veículos)
Arquivo: src/domains/vehicles/dtos.py

Testes de validação Pydantic para VehicleCreate e VehicleResponse.
"""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domains.vehicles.dtos import VehicleCreate, VehicleResponse


# ---------------------------------------------------------------------------
# VehicleCreate — happy path
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_valid_minimal():
    """Campos obrigatórios preenchidos corretamente devem criar o schema."""
    data = VehicleCreate(plate="ABC1D23", capacity=4)

    assert data.plate == "ABC1D23"
    assert data.capacity == 4
    assert data.notes is None


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_with_notes():
    """notes preenchido deve ser aceito e persistido no schema."""
    data = VehicleCreate(plate="ABC1D23", capacity=4, notes="Ar condicionado")

    assert data.notes == "Ar condicionado"


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_notes_optional():
    """Omitir notes não deve causar erro de validação."""
    data = VehicleCreate(plate="ABC1D23", capacity=4)

    assert data.notes is None


# ---------------------------------------------------------------------------
# VehicleCreate — campos obrigatórios ausentes
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_missing_plate():
    """plate é obrigatório — omitir deve lançar ValidationError."""
    with pytest.raises(ValidationError):
        VehicleCreate(capacity=4)


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_missing_capacity():
    """capacity é obrigatório — omitir deve lançar ValidationError."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="ABC1D23")


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_missing_all_fields():
    """Sem nenhum campo deve lançar ValidationError."""
    with pytest.raises(ValidationError):
        VehicleCreate()


# ---------------------------------------------------------------------------
# VehicleCreate — strings inválidas
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_empty_plate():
    """plate vazia não deve ser aceita."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="", capacity=4)


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_whitespace_only_plate():
    """plate com apenas espaços não deve ser aceita."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="   ", capacity=4)


# ---------------------------------------------------------------------------
# VehicleCreate — capacidade inválida
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_zero_capacity():
    """capacity igual a zero não deve ser aceita (mínimo 1 passageiro)."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="ABC1D23", capacity=0)


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_negative_capacity():
    """capacity negativa deve lançar ValidationError."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="ABC1D23", capacity=-1)


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_create_capacity_over_max():
    """capacity maior que 20 deve ser rejeitada — máximo permitido pelo app é 20."""
    with pytest.raises(ValidationError):
        VehicleCreate(plate="ABC1D23", capacity=21)


# ---------------------------------------------------------------------------
# VehicleResponse
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_response_structure():
    """VehicleResponse deve aceitar todos os campos e expô-los corretamente."""
    data = VehicleResponse(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        plate="ABC1D23",
        capacity=4,
        notes=None,
        status=True,
        created_at=datetime.now(),
    )

    assert data.plate == "ABC1D23"
    assert data.capacity == 4
    assert data.status is True


@pytest.mark.skip(reason="US03-TK02")
def test_vehicle_response_no_password_exposed():
    """VehicleResponse não deve ter campo password ou password_hash."""
    fields = VehicleResponse.model_fields.keys()

    assert "password" not in fields
    assert "password_hash" not in fields


# ===========================================================================
# US04 - TK02: Implementar Contratos de Atualização (VehicleUpdate)
# ===========================================================================


# ---------------------------------------------------------------------------
# VehicleUpdate — happy path
# ---------------------------------------------------------------------------


def test_vehicle_update_no_fields_is_valid():
    """VehicleUpdate sem nenhum campo deve ser válido (todos opcionais)."""
    from src.domains.vehicles.dtos import VehicleUpdate

    data = VehicleUpdate()
    assert data.plate is None
    assert data.capacity is None
    assert data.notes is None


def test_vehicle_update_plate_only():
    """VehicleUpdate com apenas plate deve ser válido."""
    from src.domains.vehicles.dtos import VehicleUpdate

    data = VehicleUpdate(plate="XYZ9W99")
    assert data.plate == "XYZ9W99"
    assert data.capacity is None


def test_vehicle_update_capacity_only():
    """VehicleUpdate com apenas capacity deve ser válido."""
    from src.domains.vehicles.dtos import VehicleUpdate

    data = VehicleUpdate(capacity=6)
    assert data.capacity == 6
    assert data.plate is None


def test_vehicle_update_all_fields():
    """VehicleUpdate com todos os campos deve ser válido."""
    from src.domains.vehicles.dtos import VehicleUpdate

    data = VehicleUpdate(plate="XYZ9W99", capacity=6, notes="Atualizado")
    assert data.plate == "XYZ9W99"
    assert data.capacity == 6
    assert data.notes == "Atualizado"


# ---------------------------------------------------------------------------
# VehicleUpdate — validações de campos quando presentes
# ---------------------------------------------------------------------------


def test_vehicle_update_empty_plate_invalid():
    """plate enviada como string vazia não deve ser aceita."""
    from src.domains.vehicles.dtos import VehicleUpdate

    with pytest.raises(ValidationError):
        VehicleUpdate(plate="")


def test_vehicle_update_whitespace_plate_invalid():
    """plate enviada como apenas espaços não deve ser aceita."""
    from src.domains.vehicles.dtos import VehicleUpdate

    with pytest.raises(ValidationError):
        VehicleUpdate(plate="   ")


def test_vehicle_update_zero_capacity_invalid():
    """capacity igual a zero não deve ser aceita na atualização."""
    from src.domains.vehicles.dtos import VehicleUpdate

    with pytest.raises(ValidationError):
        VehicleUpdate(capacity=0)


def test_vehicle_update_negative_capacity_invalid():
    """capacity negativa não deve ser aceita na atualização."""
    from src.domains.vehicles.dtos import VehicleUpdate

    with pytest.raises(ValidationError):
        VehicleUpdate(capacity=-3)


def test_vehicle_update_capacity_over_max():
    """capacity maior que 20 não deve ser aceita na atualização."""
    from src.domains.vehicles.dtos import VehicleUpdate

    with pytest.raises(ValidationError):
        VehicleUpdate(capacity=21)
