"""US09-TK02 — Tests de TripRepositoryImpl (integração SQLite)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domains.trips.entity import TripModel
from src.infrastructure.repositories.trip_repository import TripRepositoryImpl
from tests.test_trip._helpers import (
    make_driver,
    make_route,
    make_trip,
    make_vehicle,
)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_save_persists_trip(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    repo = TripRepositoryImpl(db_session)
    trip = TripModel(
        route_id=route.id,
        vehicle_id=vehicle.id,
        trip_date=datetime.now(timezone.utc),
        status="iniciada",
        started_at=datetime.now(timezone.utc),
    )
    saved = repo.save(trip)
    assert saved.id is not None
    assert saved.status == "iniciada"


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


def test_find_by_id_returns_trip(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id)

    repo = TripRepositoryImpl(db_session)
    result = repo.find_by_id(trip.id)

    assert result is not None
    assert result.id == trip.id


def test_find_by_id_returns_none_when_missing(db_session) -> None:
    repo = TripRepositoryImpl(db_session)
    assert repo.find_by_id(uuid.uuid4()) is None


# ---------------------------------------------------------------------------
# find_in_progress_by_route
# ---------------------------------------------------------------------------


def test_find_in_progress_returns_started_trip(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id, status="iniciada")

    repo = TripRepositoryImpl(db_session)
    result = repo.find_in_progress_by_route(route.id)

    assert result is not None
    assert result.id == trip.id


def test_find_in_progress_ignores_finished(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    make_trip(db_session, route.id, vehicle.id, status="finalizada")

    repo = TripRepositoryImpl(db_session)
    assert repo.find_in_progress_by_route(route.id) is None


def test_find_in_progress_returns_none_when_no_trip(db_session) -> None:
    driver = make_driver(db_session)
    make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    repo = TripRepositoryImpl(db_session)
    assert repo.find_in_progress_by_route(route.id) is None


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


def test_update_status_finishes_trip(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id, status="iniciada")

    finished_at = datetime.now(timezone.utc) + timedelta(hours=1)
    repo = TripRepositoryImpl(db_session)
    result = repo.update_status(trip.id, "finalizada", finished_at, total_km=12.5)

    assert result is not None
    assert result.status == "finalizada"
    assert result.total_km == 12.5
    # SQLite strips tzinfo on storage; re-attach for comparison (PostgreSQL preserves it)
    assert result.finished_at.replace(tzinfo=timezone.utc) == finished_at


def test_update_status_returns_none_when_missing(db_session) -> None:
    repo = TripRepositoryImpl(db_session)
    result = repo.update_status(uuid.uuid4(), "finalizada", datetime.now(timezone.utc), None)
    assert result is None
