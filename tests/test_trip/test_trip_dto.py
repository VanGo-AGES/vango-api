"""US09-TK01 — Testes dos DTOs de execução de viagem.

Critérios cobertos por TK01:

StartTripRequest
- vehicle_id: UUID, obrigatório
- trip_date: datetime, opcional (default None/agora)

FinishTripRequest
- total_km: float, opcional

TripPassangerResponse
- id, route_passanger_id: UUID
- passanger_name: str
- status: str (em {"pendente","presente","ausente"})
- pickup_address_label: str
- boarded_at, alighted_at: datetime | None
- user_phone: str — pra deeplink US13

TripResponse
- id, route_id, vehicle_id: UUID
- route_name: str
- trip_date, started_at, finished_at: datetime/datetime|None
- status: str
- total_km: float | None
- trip_passangers: list[TripPassangerResponse]

TripNextStopResponse
- stop_id, trip_passanger_id: UUID
- order_index: int
- address_label, passanger_name, passanger_phone: str
- trip_passanger_status: str
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.domains.trips.dtos import (
    FinishTripRequest,
    StartTripRequest,
    TripNextStopResponse,
    TripPassangerResponse,
    TripResponse,
)


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# StartTripRequest
# ---------------------------------------------------------------------------


def test_start_trip_request_requires_vehicle_id() -> None:
    with pytest.raises(ValidationError):
        StartTripRequest()


def test_start_trip_request_accepts_uuid_vehicle_id() -> None:
    vehicle_id = uuid.uuid4()
    dto = StartTripRequest(vehicle_id=vehicle_id)
    assert dto.vehicle_id == vehicle_id


def test_start_trip_request_trip_date_is_optional() -> None:
    dto = StartTripRequest(vehicle_id=uuid.uuid4())
    assert getattr(dto, "trip_date", None) is None


def test_start_trip_request_accepts_trip_date() -> None:
    when = _now()
    dto = StartTripRequest(vehicle_id=uuid.uuid4(), trip_date=when)
    assert dto.trip_date == when


# ---------------------------------------------------------------------------
# FinishTripRequest
# ---------------------------------------------------------------------------


def test_finish_trip_request_total_km_optional() -> None:
    dto = FinishTripRequest()
    assert getattr(dto, "total_km", None) is None


def test_finish_trip_request_accepts_total_km() -> None:
    dto = FinishTripRequest(total_km=12.5)
    assert dto.total_km == 12.5


# ---------------------------------------------------------------------------
# TripPassangerResponse
# ---------------------------------------------------------------------------


def _trip_passanger_payload(**overrides):
    base = dict(
        id=uuid.uuid4(),
        route_passanger_id=uuid.uuid4(),
        passanger_name="João",
        status="pendente",
        pickup_address_label="Rua X, 123",
        boarded_at=None,
        alighted_at=None,
        user_phone="51999999999",
    )
    base.update(overrides)
    return base


def test_trip_passanger_response_valid() -> None:
    dto = TripPassangerResponse(**_trip_passanger_payload())
    assert dto.status == "pendente"
    assert dto.boarded_at is None
    assert dto.user_phone == "51999999999"


def test_trip_passanger_response_requires_user_phone() -> None:
    payload = _trip_passanger_payload()
    payload.pop("user_phone")
    with pytest.raises(ValidationError):
        TripPassangerResponse(**payload)


def test_trip_passanger_response_accepts_boarded_and_alighted() -> None:
    now = _now()
    dto = TripPassangerResponse(**_trip_passanger_payload(boarded_at=now, alighted_at=now, status="presente"))
    assert dto.boarded_at == now
    assert dto.alighted_at == now
    assert dto.status == "presente"


# ---------------------------------------------------------------------------
# TripResponse
# ---------------------------------------------------------------------------


def _trip_payload(**overrides):
    base = dict(
        id=uuid.uuid4(),
        route_id=uuid.uuid4(),
        route_name="PUCRS Manhã",
        vehicle_id=uuid.uuid4(),
        trip_date=_now(),
        status="iniciada",
        total_km=None,
        started_at=_now(),
        finished_at=None,
        trip_passangers=[],
    )
    base.update(overrides)
    return base


def test_trip_response_valid_minimal() -> None:
    dto = TripResponse(**_trip_payload())
    assert dto.status == "iniciada"
    assert dto.total_km is None
    assert dto.trip_passangers == []


def test_trip_response_nests_trip_passangers() -> None:
    tp = TripPassangerResponse(**_trip_passanger_payload())
    dto = TripResponse(**_trip_payload(trip_passangers=[tp]))
    assert len(dto.trip_passangers) == 1
    assert dto.trip_passangers[0].passanger_name == "João"


def test_trip_response_requires_core_fields() -> None:
    with pytest.raises(ValidationError):
        TripResponse()


# ---------------------------------------------------------------------------
# TripNextStopResponse
# ---------------------------------------------------------------------------


def _next_stop_payload(**overrides):
    base = dict(
        stop_id=uuid.uuid4(),
        order_index=1,
        address_label="Rua Carazinho, 500",
        passanger_name="Bernardo",
        passanger_phone="51988887777",
        trip_passanger_id=uuid.uuid4(),
        trip_passanger_status="pendente",
    )
    base.update(overrides)
    return base


def test_trip_next_stop_response_valid() -> None:
    dto = TripNextStopResponse(**_next_stop_payload())
    assert dto.passanger_phone == "51988887777"


def test_trip_next_stop_response_requires_passanger_phone() -> None:
    payload = _next_stop_payload()
    payload.pop("passanger_phone")
    with pytest.raises(ValidationError):
        TripNextStopResponse(**payload)
