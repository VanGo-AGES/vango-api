"""US07 — Tests de StopResponse DTO e StopNotFoundError.

Campos de StopResponse (espelha a tabela `stops` do banco):
- id, route_id, route_passanger_id, address_id, order_index, type, updated_at.
"""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domains.stops.dtos import StopResponse
from src.domains.stops.errors import StopNotFoundError


def _valid_payload(**overrides):
    payload = {
        "id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "route_passanger_id": uuid.uuid4(),
        "address_id": uuid.uuid4(),
        "order_index": 1,
        "type": "embarque",
        "updated_at": datetime.now(),
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# StopResponse — atributos obrigatórios
# ---------------------------------------------------------------------------


def test_stop_response_requires_id() -> None:
    """StopResponse deve rejeitar payload sem id."""
    payload = _valid_payload()
    del payload["id"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_route_id() -> None:
    """StopResponse deve rejeitar payload sem route_id."""
    payload = _valid_payload()
    del payload["route_id"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_route_passanger_id() -> None:
    """StopResponse deve rejeitar payload sem route_passanger_id."""
    payload = _valid_payload()
    del payload["route_passanger_id"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_address_id() -> None:
    """StopResponse deve rejeitar payload sem address_id."""
    payload = _valid_payload()
    del payload["address_id"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_order_index() -> None:
    """StopResponse deve rejeitar payload sem order_index."""
    payload = _valid_payload()
    del payload["order_index"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_type() -> None:
    """StopResponse deve rejeitar payload sem type."""
    payload = _valid_payload()
    del payload["type"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


def test_stop_response_requires_updated_at() -> None:
    """StopResponse deve rejeitar payload sem updated_at."""
    payload = _valid_payload()
    del payload["updated_at"]
    with pytest.raises(ValidationError):
        StopResponse(**payload)


# ---------------------------------------------------------------------------
# StopResponse — tipos inválidos
# ---------------------------------------------------------------------------


def test_stop_response_rejects_invalid_uuid() -> None:
    """StopResponse deve rejeitar id que não é UUID."""
    with pytest.raises(ValidationError):
        StopResponse(**_valid_payload(id="not-a-uuid"))


def test_stop_response_rejects_invalid_datetime() -> None:
    """StopResponse deve rejeitar updated_at que não é datetime."""
    with pytest.raises(ValidationError):
        StopResponse(**_valid_payload(updated_at="not-a-datetime"))


def test_stop_response_rejects_invalid_order_index() -> None:
    """StopResponse deve rejeitar order_index que não é coercível a int."""
    with pytest.raises(ValidationError):
        StopResponse(**_valid_payload(order_index="not-an-int"))


# ---------------------------------------------------------------------------
# StopResponse — payload válido
# ---------------------------------------------------------------------------


def test_stop_response_valid_payload() -> None:
    """StopResponse deve aceitar payload válido completo."""
    stop = StopResponse(**_valid_payload(type="embarque"))
    assert stop.id is not None
    assert stop.route_id is not None
    assert stop.route_passanger_id is not None
    assert stop.address_id is not None
    assert stop.order_index == 1
    assert stop.type == "embarque"
    assert stop.updated_at is not None


def test_stop_response_coerces_uuid_from_string() -> None:
    """StopResponse deve aceitar UUIDs como string e converter."""
    rid = uuid.uuid4()
    stop = StopResponse(
        **_valid_payload(
            id=str(rid),
            route_id=str(uuid.uuid4()),
            route_passanger_id=str(uuid.uuid4()),
            address_id=str(uuid.uuid4()),
        )
    )
    assert stop.id == rid


def test_stop_response_from_attributes_mode() -> None:
    """StopResponse deve aceitar ORM mode (from_attributes)."""

    class FakeORM:
        id = uuid.uuid4()
        route_id = uuid.uuid4()
        route_passanger_id = uuid.uuid4()
        address_id = uuid.uuid4()
        order_index = 2
        type = "desembarque"
        updated_at = datetime.now()

    stop = StopResponse.model_validate(FakeORM(), from_attributes=True)
    assert stop.id == FakeORM.id
    assert stop.type == "desembarque"


# ---------------------------------------------------------------------------
# StopNotFoundError
# ---------------------------------------------------------------------------


def test_stop_not_found_error_inherits_exception() -> None:
    """StopNotFoundError deve herdar de Exception."""
    assert issubclass(StopNotFoundError, Exception)


def test_stop_not_found_error_default_message() -> None:
    """StopNotFoundError sem argumentos deve ter mensagem default em pt-BR."""
    err = StopNotFoundError()
    assert "stop" in str(err).lower() or "parada" in str(err).lower()


def test_stop_not_found_error_custom_message() -> None:
    """StopNotFoundError deve aceitar mensagem customizada."""
    err = StopNotFoundError("mensagem customizada")
    assert str(err) == "mensagem customizada"
