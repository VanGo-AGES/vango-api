"""Tests de AbsenceRepositoryImpl.

US09-TK04 cobre find_by_route_and_date (usado pelo start_trip).
US06-TK18 cobre save + find_for_route_passanger_on_date (aviso de falta
originado pelo passageiro/guardian na tela 2.3).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.domains.trips.entity import AbsenceModel
from src.infrastructure.repositories.absence_repository import AbsenceRepositoryImpl
from tests.test_trip._helpers import (
    make_absence,
    make_driver,
    make_passenger,
    make_route,
    make_rp,
)


@pytest.mark.skip(reason="US09-TK04")
def test_find_by_route_and_date_returns_absences_of_that_day(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    p1 = make_passenger(db_session, "A")
    p2 = make_passenger(db_session, "B")
    rp1 = make_rp(db_session, route.id, p1.id, status="accepted")
    rp2 = make_rp(db_session, route.id, p2.id, status="accepted")

    target_day = datetime(2026, 4, 22, 0, 0, tzinfo=timezone.utc)
    absence1 = make_absence(db_session, rp1.id, target_day)
    absence2 = make_absence(db_session, rp2.id, target_day + timedelta(hours=5))
    make_absence(db_session, rp1.id, target_day + timedelta(days=1))  # outro dia — ignorado

    repo = AbsenceRepositoryImpl(db_session)
    result = repo.find_by_route_and_date(route.id, target_day)

    ids = {a.id for a in result}
    assert absence1.id in ids
    assert absence2.id in ids
    assert len(result) == 2


@pytest.mark.skip(reason="US09-TK04")
def test_find_by_route_and_date_returns_empty_when_nothing(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)

    repo = AbsenceRepositoryImpl(db_session)
    result = repo.find_by_route_and_date(route.id, datetime.now(timezone.utc))

    assert result == []


@pytest.mark.skip(reason="US09-TK04")
def test_find_by_route_and_date_filters_by_route(db_session) -> None:
    driver = make_driver(db_session)
    route_a = make_route(db_session, driver.id)
    route_b = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp_a = make_rp(db_session, route_a.id, passenger.id, status="accepted")
    rp_b = make_rp(db_session, route_b.id, passenger.id, status="accepted")

    day = datetime(2026, 4, 22, 8, 0, tzinfo=timezone.utc)
    make_absence(db_session, rp_a.id, day)
    make_absence(db_session, rp_b.id, day)

    repo = AbsenceRepositoryImpl(db_session)
    result = repo.find_by_route_and_date(route_a.id, day)

    assert len(result) == 1
    assert result[0].route_passanger_id == rp_a.id


@pytest.mark.skip(reason="US09-TK04")
def test_find_by_route_and_date_handles_missing_route(db_session) -> None:
    repo = AbsenceRepositoryImpl(db_session)
    assert repo.find_by_route_and_date(uuid.uuid4(), datetime.now(timezone.utc)) == []


# ===========================================================================
# US06-TK18 — save + find_for_route_passanger_on_date
# ===========================================================================


@pytest.mark.skip(reason="US06-TK18")
def test_save_persists_new_absence(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")

    repo = AbsenceRepositoryImpl(db_session)
    absence = AbsenceModel(
        route_passanger_id=rp.id,
        absence_date=datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc),
        reason="Consulta",
    )
    saved = repo.save(absence)

    assert saved.id is not None
    assert saved.route_passanger_id == rp.id
    assert saved.reason == "Consulta"


@pytest.mark.skip(reason="US06-TK18")
def test_save_sets_created_at_automatically(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")

    repo = AbsenceRepositoryImpl(db_session)
    saved = repo.save(
        AbsenceModel(
            route_passanger_id=rp.id,
            absence_date=datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc),
        )
    )

    assert saved.created_at is not None


@pytest.mark.skip(reason="US06-TK18")
def test_find_for_route_passanger_on_date_returns_existing(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")

    day = datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc)
    make_absence(db_session, rp.id, day)

    repo = AbsenceRepositoryImpl(db_session)
    result = repo.find_for_route_passanger_on_date(rp.id, day)

    assert result is not None
    assert result.route_passanger_id == rp.id


@pytest.mark.skip(reason="US06-TK18")
def test_find_for_route_passanger_on_date_ignores_other_days(db_session) -> None:
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")

    day = datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc)
    make_absence(db_session, rp.id, day + timedelta(days=1))

    repo = AbsenceRepositoryImpl(db_session)
    assert repo.find_for_route_passanger_on_date(rp.id, day) is None


@pytest.mark.skip(reason="US06-TK18")
def test_find_for_route_passanger_on_date_matches_by_day_interval(db_session) -> None:
    """Deve achar absence gravada em qualquer hora do mesmo dia."""
    driver = make_driver(db_session)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")

    stored_at = datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc)
    make_absence(db_session, rp.id, stored_at)

    repo = AbsenceRepositoryImpl(db_session)
    queried_at = datetime(2026, 4, 23, 0, 0, tzinfo=timezone.utc)
    assert repo.find_for_route_passanger_on_date(rp.id, queried_at) is not None


@pytest.mark.skip(reason="US06-TK18")
def test_find_for_route_passanger_on_date_missing_returns_none(db_session) -> None:
    repo = AbsenceRepositoryImpl(db_session)
    assert (
        repo.find_for_route_passanger_on_date(
            uuid.uuid4(), datetime.now(timezone.utc)
        )
        is None
    )
