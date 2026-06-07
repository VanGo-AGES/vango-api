"""US15-TK02 — TripMetricsRepository (agregação SQL).

Remova o skip rodando:

Os testes usam a sessão SQLite em memória (fixture `db_session` do conftest)
e as factories de `tests/test_trip/_helpers.py`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.infrastructure.repositories.trip_metrics_repository import TripMetricsRepositoryImpl
from tests.test_trip._helpers import (
    make_driver,
    make_passenger,
    make_route,
    make_rp,
    make_trip,
    make_trip_passanger,
    make_vehicle,
)

WINDOW_START = datetime(2025, 8, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2025, 8, 31, 23, 59, 59, tzinfo=timezone.utc)


def _finish(trip, started, minutes, km):
    trip.started_at = started
    trip.finished_at = started + timedelta(minutes=minutes)
    trip.total_km = km


def test_aggregate_sums_km_duration_and_counts(db_session):
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    t1 = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc))
    _finish(t1, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=30, km=10.0)
    t2 = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 12, 7, 0, tzinfo=timezone.utc))
    _finish(t2, datetime(2025, 8, 12, 7, 0, tzinfo=timezone.utc), minutes=20, km=5.5)

    p1 = make_passenger(db_session)
    p2 = make_passenger(db_session)
    rp1 = make_rp(db_session, route.id, p1.id)
    rp2 = make_rp(db_session, route.id, p2.id)
    make_trip_passanger(db_session, t1.id, rp1.id, status="presente")
    make_trip_passanger(db_session, t1.id, rp2.id, status="ausente")
    make_trip_passanger(db_session, t2.id, rp1.id, status="presente")
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.total_km == pytest.approx(15.5)
    assert agg.total_duration_seconds == (30 + 20) * 60
    assert agg.passengers == 2  # apenas os "presente"
    assert agg.trips == 2


def test_aggregate_excludes_other_drivers(db_session):
    driver = make_driver(db_session)
    other = make_driver(db_session)
    v1 = make_vehicle(db_session, driver.id)
    v2 = make_vehicle(db_session, other.id)
    r1 = make_route(db_session, driver.id)
    r2 = make_route(db_session, other.id)

    t1 = make_trip(db_session, r1.id, v1.id, status="finalizada", trip_date=datetime(2025, 8, 10, tzinfo=timezone.utc))
    _finish(t1, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=30, km=10.0)
    t2 = make_trip(db_session, r2.id, v2.id, status="finalizada", trip_date=datetime(2025, 8, 10, tzinfo=timezone.utc))
    _finish(t2, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=99, km=99.0)
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.total_km == pytest.approx(10.0)
    assert agg.trips == 1


def test_aggregate_ignores_unfinished_and_out_of_range(db_session):
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    # finalizada dentro do intervalo
    t_in = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 10, tzinfo=timezone.utc))
    _finish(t_in, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=30, km=10.0)
    # em andamento (não conta)
    make_trip(db_session, route.id, vehicle.id, status="iniciada", trip_date=datetime(2025, 8, 11, tzinfo=timezone.utc))
    # finalizada fora do intervalo (não conta)
    t_out = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 7, 10, tzinfo=timezone.utc))
    _finish(t_out, datetime(2025, 7, 10, 7, 0, tzinfo=timezone.utc), minutes=40, km=40.0)
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.trips == 1
    assert agg.total_km == pytest.approx(10.0)


def test_aggregate_returns_zeros_when_empty(db_session):
    driver = make_driver(db_session)
    repo = TripMetricsRepositoryImpl(db_session)

    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.total_km == 0
    assert agg.total_duration_seconds == 0
    assert agg.passengers == 0
    assert agg.trips == 0


def test_aggregate_treats_null_total_km_as_zero(db_session):
    """total_km é nullable (finish_trip aceita None). SUM de NULLs não pode
    virar None — deve ser tratado como 0, sem deixar de contar a trip."""
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    t1 = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc))
    t1.started_at = datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc)
    t1.finished_at = t1.started_at + timedelta(minutes=30)
    t1.total_km = None  # motorista finalizou sem registrar km
    t2 = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 11, 7, 0, tzinfo=timezone.utc))
    _finish(t2, datetime(2025, 8, 11, 7, 0, tzinfo=timezone.utc), minutes=20, km=5.0)
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.total_km == pytest.approx(5.0)
    assert agg.trips == 2
    assert agg.total_duration_seconds == (30 + 20) * 60


def test_aggregate_window_is_inclusive_by_trip_date(db_session):
    """O intervalo [start, end] é inclusivo nas bordas e usa trip_date."""
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    t_start = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=WINDOW_START)
    _finish(t_start, WINDOW_START, minutes=10, km=1.0)
    t_end = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=WINDOW_END)
    _finish(t_end, WINDOW_END, minutes=10, km=2.0)
    t_after = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc))
    _finish(t_after, datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc), minutes=10, km=99.0)
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.trips == 2
    assert agg.total_km == pytest.approx(3.0)


def test_aggregate_excludes_cancelled_trips(db_session):
    """Só trips 'finalizada' contam — 'cancelada' fica de fora."""
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    t_fin = make_trip(db_session, route.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 10, tzinfo=timezone.utc))
    _finish(t_fin, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=30, km=10.0)
    t_can = make_trip(db_session, route.id, vehicle.id, status="cancelada", trip_date=datetime(2025, 8, 11, tzinfo=timezone.utc))
    t_can.total_km = 99.0
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.trips == 1
    assert agg.total_km == pytest.approx(10.0)


def test_aggregate_sums_across_driver_routes(db_session):
    """As métricas são por motorista: trips de rotas diferentes dele somam juntas."""
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    r1 = make_route(db_session, driver.id)
    r2 = make_route(db_session, driver.id)

    t1 = make_trip(db_session, r1.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 10, tzinfo=timezone.utc))
    _finish(t1, datetime(2025, 8, 10, 7, 0, tzinfo=timezone.utc), minutes=30, km=10.0)
    t2 = make_trip(db_session, r2.id, vehicle.id, status="finalizada", trip_date=datetime(2025, 8, 11, tzinfo=timezone.utc))
    _finish(t2, datetime(2025, 8, 11, 7, 0, tzinfo=timezone.utc), minutes=20, km=5.0)

    p1 = make_passenger(db_session)
    p2 = make_passenger(db_session)
    rp1 = make_rp(db_session, r1.id, p1.id)
    rp2 = make_rp(db_session, r2.id, p2.id)
    make_trip_passanger(db_session, t1.id, rp1.id, status="presente")
    make_trip_passanger(db_session, t2.id, rp2.id, status="presente")
    db_session.flush()

    repo = TripMetricsRepositoryImpl(db_session)
    agg = repo.aggregate_driver_metrics(driver.id, WINDOW_START, WINDOW_END)

    assert agg.trips == 2
    assert agg.total_km == pytest.approx(15.0)
    assert agg.passengers == 2
    assert agg.total_duration_seconds == (30 + 20) * 60
