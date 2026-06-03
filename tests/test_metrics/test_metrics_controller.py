"""US15-TK04 — Controller GET /metrics/reports (unidade + integração).

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US15-TK04")/d' tests/test_metrics/test_metrics_controller.py

- Testes unitários mockam o MetricsService via dependency_override.
- Teste de integração sobrescreve get_db pela sessão SQLite e exercita
  HTTP -> controller -> service -> repositório real.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.domains.metrics.dtos import MetricsReportResponse, ReportPeriod
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.metrics_dependencies import get_metrics_service
from src.main import fastapi_app as app
from tests.test_trip._helpers import (
    make_driver,
    make_passenger,
    make_route,
    make_rp,
    make_trip,
    make_trip_passanger,
    make_vehicle,
)

client = TestClient(app, raise_server_exceptions=False)
DRIVER_ID = str(uuid.uuid4())
HEADERS = {"X-User-Id": DRIVER_ID, "X-User-Role": "driver"}


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_returns_200_and_body():
    fake = MetricsReportResponse(
        distance=15.5,
        duration=50,
        passengers=15,
        trips=4,
        period=ReportPeriod.WEEK,
        start_date=date(2025, 8, 17),
        end_date=date(2025, 8, 23),
    )
    service = type("S", (), {"get_report": lambda self, *a, **k: fake})()
    app.dependency_overrides[get_metrics_service] = lambda: service
    try:
        resp = client.get(
            "/metrics/reports",
            params={"period": "week", "start_date": "2025-08-17", "end_date": "2025-08-23"},
            headers=HEADERS,
        )
    finally:
        app.dependency_overrides.pop(get_metrics_service, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["distance"] == 15.5
    assert body["duration"] == 50
    assert body["passengers"] == 15
    assert body["trips"] == 4


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_invalid_period_returns_422():
    resp = client.get(
        "/metrics/reports",
        params={"period": "decade", "start_date": "2025-08-17"},
        headers=HEADERS,
    )
    assert resp.status_code == 422


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_missing_start_date_returns_422():
    resp = client.get("/metrics/reports", params={"period": "week"}, headers=HEADERS)
    assert resp.status_code == 422


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_malformed_date_returns_422():
    resp = client.get(
        "/metrics/reports",
        params={"period": "day", "start_date": "notadate"},
        headers=HEADERS,
    )
    assert resp.status_code == 422


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_passes_parsed_args_to_service():
    """O controller deve repassar driver_id (do header), period (enum) e datas
    parseadas para o service."""
    captured = {}

    def _get_report(self, driver_id, period, start_date, end_date=None):
        captured.update(driver_id=driver_id, period=period, start_date=start_date, end_date=end_date)
        return MetricsReportResponse(
            distance=0,
            duration=0,
            passengers=0,
            trips=0,
            period=period,
            start_date=start_date,
            end_date=end_date or start_date,
        )

    service = type("S", (), {"get_report": _get_report})()
    app.dependency_overrides[get_metrics_service] = lambda: service
    try:
        resp = client.get(
            "/metrics/reports",
            params={"period": "week", "start_date": "2025-08-17", "end_date": "2025-08-23"},
            headers=HEADERS,
        )
    finally:
        app.dependency_overrides.pop(get_metrics_service, None)

    assert resp.status_code == 200
    assert captured["driver_id"] == uuid.UUID(DRIVER_ID)
    assert captured["period"] == ReportPeriod.WEEK
    assert captured["start_date"] == date(2025, 8, 17)
    assert captured["end_date"] == date(2025, 8, 23)


@pytest.mark.skip(reason="US15-TK04")
def test_get_reports_integration_aggregates_real_data(db_session):
    from datetime import datetime, timedelta, timezone

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    start = datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc)
    trip = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=start)
    trip.started_at = start
    trip.finished_at = start + timedelta(minutes=32)
    trip.total_km = 10.0
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id)
    make_trip_passanger(db_session, trip.id, rp.id, status="presente")
    db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.get(
            "/metrics/reports",
            params={"period": "month", "start_date": "2025-08-01"},
            headers={"X-User-Id": str(driver.id), "X-User-Role": "driver"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["distance"] == pytest.approx(10.0)
    assert body["duration"] == 32
    assert body["passengers"] == 1
    assert body["trips"] == 1
