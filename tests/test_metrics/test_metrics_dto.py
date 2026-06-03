"""US15-TK01 — DTOs de Métricas & Relatórios.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US15-TK01")/d' tests/test_metrics/test_metrics_dto.py
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.domains.metrics.dtos import MetricsReportResponse, ReportPeriod


@pytest.mark.skip(reason="US15-TK01")
def test_report_period_values():
    assert ReportPeriod.DAY.value == "day"
    assert ReportPeriod.WEEK.value == "week"
    assert ReportPeriod.MONTH.value == "month"


@pytest.mark.skip(reason="US15-TK01")
def test_metrics_report_response_holds_all_fields():
    dto = MetricsReportResponse(
        distance=10.5,
        duration=32,
        passengers=15,
        trips=4,
        period=ReportPeriod.WEEK,
        start_date=date(2025, 8, 17),
        end_date=date(2025, 8, 23),
    )

    assert dto.distance == 10.5
    assert dto.duration == 32
    assert dto.passengers == 15
    assert dto.trips == 4
    assert dto.period == ReportPeriod.WEEK
    assert dto.start_date == date(2025, 8, 17)
    assert dto.end_date == date(2025, 8, 23)


@pytest.mark.skip(reason="US15-TK01")
def test_metrics_report_response_defaults_are_zeroed():
    """Período sem viagens deve conseguir retornar zeros."""
    dto = MetricsReportResponse(
        period=ReportPeriod.DAY,
        start_date=date(2025, 8, 17),
        end_date=date(2025, 8, 17),
    )

    assert dto.distance == 0
    assert dto.duration == 0
    assert dto.passengers == 0
    assert dto.trips == 0


@pytest.mark.skip(reason="US15-TK01")
def test_metrics_report_response_json_contract_for_frontend():
    """O JSON serializado precisa bater com o que o FE consome:
    números crus, period como string e datas em ISO (YYYY-MM-DD)."""
    dto = MetricsReportResponse(
        distance=10.5,
        duration=32,
        passengers=15,
        trips=4,
        period=ReportPeriod.MONTH,
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 31),
    )

    data = dto.model_dump(mode="json")
    assert data["distance"] == 10.5
    assert data["duration"] == 32
    assert data["passengers"] == 15
    assert data["trips"] == 4
    assert data["period"] == "month"
    assert data["start_date"] == "2025-08-01"
    assert data["end_date"] == "2025-08-31"


@pytest.mark.skip(reason="US15-TK01")
def test_metrics_report_response_rejects_invalid_period():
    """period fora de day/week/month deve falhar a validação."""
    with pytest.raises(ValidationError):
        MetricsReportResponse(
            distance=0,
            duration=0,
            passengers=0,
            trips=0,
            period="decade",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 1),
        )
