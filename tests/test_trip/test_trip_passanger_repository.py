"""US09-TK03 — Tests de TripPassangerRepositoryImpl."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domains.trips.entity import TripPassangerModel
from src.infrastructure.repositories.trip_passanger_repository import (
    TripPassangerRepositoryImpl,
)
from tests.test_trip._helpers import (
    make_address,
    make_driver,
    make_passenger,
    make_route,
    make_rp,
    make_stop,
    make_trip,
    make_trip_passanger,
    make_vehicle,
)


# ---------------------------------------------------------------------------
# save_all
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK03")
def test_save_all_persists_all_trip_passangers(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    p1 = make_passenger(db_session, "A")
    p2 = make_passenger(db_session, "B")
    rp1 = make_rp(db_session, route.id, p1.id, status="accepted")
    rp2 = make_rp(db_session, route.id, p2.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)

    repo = TripPassangerRepositoryImpl(db_session)
    result = repo.save_all(
        [
            TripPassangerModel(trip_id=trip.id, route_passanger_id=rp1.id, status="pendente"),
            TripPassangerModel(trip_id=trip.id, route_passanger_id=rp2.id, status="ausente"),
        ]
    )
    assert len(result) == 2
    assert {tp.status for tp in result} == {"pendente", "ausente"}


# ---------------------------------------------------------------------------
# find_by_id / find_by_trip
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK03")
def test_find_by_id_returns_model(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id)

    repo = TripPassangerRepositoryImpl(db_session)
    assert repo.find_by_id(tp.id) is not None


@pytest.mark.skip(reason="US09-TK03")
def test_find_by_id_missing_returns_none(db_session) -> None:
    repo = TripPassangerRepositoryImpl(db_session)
    assert repo.find_by_id(uuid.uuid4()) is None


@pytest.mark.skip(reason="US09-TK03")
def test_find_by_trip_orders_by_stop_order_index(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    p1 = make_passenger(db_session, "A")
    p2 = make_passenger(db_session, "B")
    rp1 = make_rp(db_session, route.id, p1.id, status="accepted")
    rp2 = make_rp(db_session, route.id, p2.id, status="accepted")
    addr1 = make_address(db_session, p1.id)
    addr2 = make_address(db_session, p2.id)
    make_stop(db_session, route.id, rp1.id, addr1.id, order_index=2)
    make_stop(db_session, route.id, rp2.id, addr2.id, order_index=1)
    trip = make_trip(db_session, route.id, vehicle.id)
    tp1 = make_trip_passanger(db_session, trip.id, rp1.id)
    tp2 = make_trip_passanger(db_session, trip.id, rp2.id)

    repo = TripPassangerRepositoryImpl(db_session)
    result = repo.find_by_trip(trip.id)

    assert [x.id for x in result] == [tp2.id, tp1.id]


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK03")
def test_update_status_sets_boarded_at(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    boarded_at = datetime.now(timezone.utc)
    repo = TripPassangerRepositoryImpl(db_session)
    updated = repo.update_status(tp.id, "presente", boarded_at=boarded_at)

    assert updated is not None
    assert updated.status == "presente"
    assert updated.boarded_at == boarded_at
    assert updated.alighted_at is None


@pytest.mark.skip(reason="US09-TK03")
def test_update_status_sets_absent(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    repo = TripPassangerRepositoryImpl(db_session)
    updated = repo.update_status(tp.id, "ausente")

    assert updated is not None
    assert updated.status == "ausente"
    assert updated.boarded_at is None


@pytest.mark.skip(reason="US09-TK03")
def test_update_status_returns_none_when_missing(db_session) -> None:
    repo = TripPassangerRepositoryImpl(db_session)
    assert repo.update_status(uuid.uuid4(), "presente") is None


# ---------------------------------------------------------------------------
# bulk_alight_presents
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK03")
def test_bulk_alight_presents_fills_missing_alighted_at(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    p1 = make_passenger(db_session, "A")
    p2 = make_passenger(db_session, "B")
    p3 = make_passenger(db_session, "C")
    rp1 = make_rp(db_session, route.id, p1.id, status="accepted")
    rp2 = make_rp(db_session, route.id, p2.id, status="accepted")
    rp3 = make_rp(db_session, route.id, p3.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp1 = make_trip_passanger(db_session, trip.id, rp1.id, status="presente")
    tp2 = make_trip_passanger(db_session, trip.id, rp2.id, status="ausente")
    tp3 = make_trip_passanger(db_session, trip.id, rp3.id, status="presente")

    now = datetime.now(timezone.utc)
    repo = TripPassangerRepositoryImpl(db_session)
    affected = repo.bulk_alight_presents(trip.id, now)

    db_session.refresh(tp1)
    db_session.refresh(tp2)
    db_session.refresh(tp3)

    assert affected == 2
    assert tp1.alighted_at == now
    assert tp3.alighted_at == now
    assert tp2.alighted_at is None


@pytest.mark.skip(reason="US09-TK03")
def test_bulk_alight_presents_skips_already_alighted(db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    earlier = datetime.now(timezone.utc)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="presente")
    tp.alighted_at = earlier
    db_session.flush()

    later = datetime.now(timezone.utc)
    repo = TripPassangerRepositoryImpl(db_session)
    affected = repo.bulk_alight_presents(trip.id, later)

    db_session.refresh(tp)
    assert affected == 0
    assert tp.alighted_at == earlier
