"""US09-TK04 — Tests de AbsenceRepositoryImpl.

Apenas find_by_route_and_date. Criação/listagem full de absences é tratada
em outra US.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

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
