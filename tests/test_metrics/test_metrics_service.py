"""US15-TK03 — MetricsService.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US15-TK03")/d' tests/test_metrics/test_metrics_service.py

O service mocka o ITripMetricsRepository — não toca no banco.
"""

from datetime import date, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.domains.metrics.dtos import MetricsReportResponse, ReportPeriod
from src.domains.metrics.repository import MetricsAggregate
from src.domains.metrics.service import MetricsService


def _service_with_aggregate(agg: MetricsAggregate):
    repo = Mock()
    repo.aggregate_driver_metrics.return_value = agg
    return MetricsService(repo), repo


def _called_window(repo):
    """Extrai (start, end) passados ao repo, seja posicional ou nomeado."""
    call = repo.aggregate_driver_metrics.call_args
    start = call.kwargs.get("start", call.args[1] if len(call.args) > 1 else None)
    end = call.kwargs.get("end", call.args[2] if len(call.args) > 2 else None)
    return start, end


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_maps_aggregate_to_dto():
    agg = MetricsAggregate(total_km=15.5, total_duration_seconds=3000, passengers=15, trips=4)
    service, _ = _service_with_aggregate(agg)

    result = service.get_report(uuid4(), ReportPeriod.WEEK, date(2025, 8, 17), date(2025, 8, 23))

    assert isinstance(result, MetricsReportResponse)
    assert result.distance == pytest.approx(15.5)
    assert result.duration == 50  # 3000s -> 50 min
    assert result.passengers == 15
    assert result.trips == 4
    assert result.period == ReportPeriod.WEEK


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_day_uses_single_day_window():
    agg = MetricsAggregate(total_km=10.0, total_duration_seconds=1920, passengers=3, trips=1)
    service, repo = _service_with_aggregate(agg)

    service.get_report(uuid4(), ReportPeriod.DAY, date(2025, 8, 17))

    _, kwargs = repo.aggregate_driver_metrics.call_args
    args = repo.aggregate_driver_metrics.call_args.args
    start = kwargs.get("start", args[1] if len(args) > 1 else None)
    end = kwargs.get("end", args[2] if len(args) > 2 else None)
    assert isinstance(start, datetime) and isinstance(end, datetime)
    assert start.date() == date(2025, 8, 17)
    assert end.date() == date(2025, 8, 17)


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_month_spans_full_month():
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=0, passengers=0, trips=0)
    service, repo = _service_with_aggregate(agg)

    service.get_report(uuid4(), ReportPeriod.MONTH, date(2025, 8, 15))

    args = repo.aggregate_driver_metrics.call_args.args
    kwargs = repo.aggregate_driver_metrics.call_args.kwargs
    start = kwargs.get("start", args[1] if len(args) > 1 else None)
    end = kwargs.get("end", args[2] if len(args) > 2 else None)
    assert start.date() == date(2025, 8, 1)
    assert end.date() == date(2025, 8, 31)


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_returns_zeros_when_no_trips():
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=0, passengers=0, trips=0)
    service, _ = _service_with_aggregate(agg)

    result = service.get_report(uuid4(), ReportPeriod.DAY, date(2025, 8, 17))

    assert result.distance == 0
    assert result.duration == 0
    assert result.passengers == 0
    assert result.trips == 0


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_week_uses_explicit_end_date():
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=0, passengers=0, trips=0)
    service, repo = _service_with_aggregate(agg)

    service.get_report(uuid4(), ReportPeriod.WEEK, date(2025, 8, 17), date(2025, 8, 23))

    start, end = _called_window(repo)
    assert start.date() == date(2025, 8, 17)
    assert end.date() == date(2025, 8, 23)


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_week_without_end_defaults_to_seven_days():
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=0, passengers=0, trips=0)
    service, repo = _service_with_aggregate(agg)

    service.get_report(uuid4(), ReportPeriod.WEEK, date(2025, 8, 17))

    start, end = _called_window(repo)
    assert start.date() == date(2025, 8, 17)
    assert end.date() == date(2025, 8, 23)  # start + 6 dias


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_window_covers_full_day_bounds():
    """start no começo do dia (00:00:00) e end no fim do dia (23:59),
    para casar com o filtro inclusivo do repositório (US15-TK02)."""
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=0, passengers=0, trips=0)
    service, repo = _service_with_aggregate(agg)

    service.get_report(uuid4(), ReportPeriod.DAY, date(2025, 8, 17))

    start, end = _called_window(repo)
    assert (start.hour, start.minute, start.second) == (0, 0, 0)
    assert (end.hour, end.minute) == (23, 59)


@pytest.mark.skip(reason="US15-TK03")
def test_get_report_rounds_duration_to_nearest_minute():
    """duration é minutos arredondados, não truncados: 110s -> 2 min."""
    agg = MetricsAggregate(total_km=0.0, total_duration_seconds=110, passengers=0, trips=1)
    service, _ = _service_with_aggregate(agg)

    result = service.get_report(uuid4(), ReportPeriod.DAY, date(2025, 8, 17))

    assert result.duration == 2
