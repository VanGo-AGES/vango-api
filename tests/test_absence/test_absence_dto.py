"""US06-TK18 — Testes dos DTOs de Absence.

Valida CreateAbsenceRequest (payload enviado pelo passageiro) e AbsenceResponse
(representação persistida).
"""

import uuid
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.domains.absences.dtos import AbsenceResponse, CreateAbsenceRequest


# ---------------------------------------------------------------------------
# CreateAbsenceRequest
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK18")
def test_create_absence_request_minimal_payload() -> None:
    payload = {
        "route_id": uuid.uuid4(),
        "absence_date": date(2026, 4, 23),
    }
    dto = CreateAbsenceRequest(**payload)
    assert dto.route_id == payload["route_id"]
    assert dto.absence_date == payload["absence_date"]
    assert dto.dependent_id is None
    assert dto.reason is None


@pytest.mark.skip(reason="US06-TK18")
def test_create_absence_request_with_dependent_and_reason() -> None:
    payload = {
        "route_id": uuid.uuid4(),
        "absence_date": date(2026, 4, 23),
        "dependent_id": uuid.uuid4(),
        "reason": "Consulta médica",
    }
    dto = CreateAbsenceRequest(**payload)
    assert dto.dependent_id == payload["dependent_id"]
    assert dto.reason == "Consulta médica"


@pytest.mark.skip(reason="US06-TK18")
def test_create_absence_request_missing_route_id_raises() -> None:
    with pytest.raises(ValidationError):
        CreateAbsenceRequest(absence_date=date(2026, 4, 23))


@pytest.mark.skip(reason="US06-TK18")
def test_create_absence_request_missing_absence_date_raises() -> None:
    with pytest.raises(ValidationError):
        CreateAbsenceRequest(route_id=uuid.uuid4())


@pytest.mark.skip(reason="US06-TK18")
def test_create_absence_request_reason_max_length_enforced() -> None:
    with pytest.raises(ValidationError):
        CreateAbsenceRequest(
            route_id=uuid.uuid4(),
            absence_date=date(2026, 4, 23),
            reason="x" * 1000,
        )


# ---------------------------------------------------------------------------
# AbsenceResponse
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK18")
def test_absence_response_serializes_full_payload() -> None:
    payload = {
        "id": uuid.uuid4(),
        "route_passanger_id": uuid.uuid4(),
        "absence_date": datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc),
        "reason": "Consulta",
        "created_at": datetime(2026, 4, 22, 15, 30, tzinfo=timezone.utc),
    }
    dto = AbsenceResponse(**payload)
    assert dto.id == payload["id"]
    assert dto.route_passanger_id == payload["route_passanger_id"]
    assert dto.reason == "Consulta"


@pytest.mark.skip(reason="US06-TK18")
def test_absence_response_accepts_none_reason() -> None:
    dto = AbsenceResponse(
        id=uuid.uuid4(),
        route_passanger_id=uuid.uuid4(),
        absence_date=datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc),
        reason=None,
        created_at=datetime.now(tz=timezone.utc),
    )
    assert dto.reason is None


@pytest.mark.skip(reason="US06-TK18")
def test_absence_response_from_attributes() -> None:
    """Deve construir via model_validate a partir de um AbsenceModel ORM."""

    class FakeOrm:
        id = uuid.uuid4()
        route_passanger_id = uuid.uuid4()
        absence_date = datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc)
        reason = None
        created_at = datetime.now(tz=timezone.utc)

    dto = AbsenceResponse.model_validate(FakeOrm())
    assert dto.id == FakeOrm.id
