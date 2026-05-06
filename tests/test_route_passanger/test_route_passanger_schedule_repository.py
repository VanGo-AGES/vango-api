"""US08-TK02 — Testes do RoutePassangerScheduleRepositoryImpl.

Arquivo:  src/infrastructure/repositories/route_passanger_schedule_repository.py
Métodos:  save_many, find_by_route_passanger_id, delete_by_route_passanger_id,
          replace
"""

import uuid
from datetime import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database import Base


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


def make_user(session, role: str = "guardian", name: str = "Usuário"):
    from src.domains.users.entity import UserModel

    user = UserModel(
        id=uuid.uuid4(),
        name=name,
        email=f"user_{uuid.uuid4().hex[:6]}@test.com",
        phone="54999999999",
        password_hash="hashed",
        role=role,
    )
    session.add(user)
    session.flush()
    return user


def make_address(session, user_id: uuid.UUID, label: str = "Casa"):
    from src.domains.addresses.entity import AddressModel

    address = AddressModel(
        id=uuid.uuid4(),
        user_id=user_id,
        label=label,
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    session.add(address)
    session.flush()
    return address


def make_route(session, driver_id, origin_id, destination_id, **kwargs):
    from src.domains.routes.entity import RouteModel

    defaults = {
        "id": uuid.uuid4(),
        "driver_id": driver_id,
        "origin_address_id": origin_id,
        "destination_address_id": destination_id,
        "name": "PUCRS",
        "route_type": "outbound",
        "recurrence": "seg,ter,qua,qui,sex",
        "max_passengers": 5,
        "expected_time": time(8, 0),
        "status": "inativa",
        "invite_code": uuid.uuid4().hex[:8],
    }
    defaults.update(kwargs)
    route = RouteModel(**defaults)
    session.add(route)
    session.flush()
    return route


def make_route_passanger(
    session,
    route_id,
    user_id,
    status: str = "pending",
    dependent_id=None,
    pickup_address_id: uuid.UUID | None = None,
):
    from src.domains.route_passangers.entity import RoutePassangerModel

    if pickup_address_id is None:
        pickup_address_id = make_address(session, user_id, "Pickup").id

    rp = RoutePassangerModel(
        id=uuid.uuid4(),
        route_id=route_id,
        user_id=user_id,
        dependent_id=dependent_id,
        status=status,
        pickup_address_id=pickup_address_id,
    )
    session.add(rp)
    session.flush()
    return rp


def make_schedule(rp_id, address_id, day: str):
    from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel

    return RoutePassangerScheduleModel(
        id=uuid.uuid4(),
        route_passanger_id=rp_id,
        address_id=address_id,
        day_of_week=day,
    )


def setup_rp(db_session):
    """Cria driver + route + passenger + rp e retorna (rp, address)."""
    driver = make_user(db_session, role="driver", name="Driver")
    passenger = make_user(db_session, name="Passenger")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    pickup = make_address(db_session, passenger.id, "Casa Passenger")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id)
    return rp, pickup


# ---------------------------------------------------------------------------
# save_many
# ---------------------------------------------------------------------------


def test_schedule_repository_save_many_persists_schedules(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp, pickup = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)

    saved = repo.save_many([
        make_schedule(rp.id, pickup.id, "monday"),
        make_schedule(rp.id, pickup.id, "wednesday"),
    ])

    assert len(saved) == 2
    assert {s.day_of_week for s in saved} == {"monday", "wednesday"}


def test_schedule_repository_save_many_empty_list_returns_empty(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    assert repo.save_many([]) == []


# ---------------------------------------------------------------------------
# find_by_route_passanger_id
# ---------------------------------------------------------------------------


def test_schedule_repository_find_by_rp_returns_only_rp_schedules(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp, pickup = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([
        make_schedule(rp.id, pickup.id, "monday"),
        make_schedule(rp.id, pickup.id, "tuesday"),
    ])

    result = repo.find_by_route_passanger_id(rp.id)
    assert len(result) == 2
    assert {s.day_of_week for s in result} == {"monday", "tuesday"}


def test_schedule_repository_find_by_rp_empty_returns_empty_list(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    assert repo.find_by_route_passanger_id(uuid.uuid4()) == []


def test_schedule_repository_find_by_rp_filters_by_rp(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp_a, pickup_a = setup_rp(db_session)
    rp_b, pickup_b = setup_rp(db_session)

    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([make_schedule(rp_a.id, pickup_a.id, "monday")])
    repo.save_many([make_schedule(rp_b.id, pickup_b.id, "friday")])

    result_a = repo.find_by_route_passanger_id(rp_a.id)
    assert len(result_a) == 1
    assert result_a[0].day_of_week == "monday"


# ---------------------------------------------------------------------------
# delete_by_route_passanger_id
# ---------------------------------------------------------------------------


def test_schedule_repository_delete_by_rp_removes_all(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp, pickup = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([
        make_schedule(rp.id, pickup.id, "monday"),
        make_schedule(rp.id, pickup.id, "tuesday"),
        make_schedule(rp.id, pickup.id, "friday"),
    ])

    removed = repo.delete_by_route_passanger_id(rp.id)

    assert removed == 3
    assert repo.find_by_route_passanger_id(rp.id) == []


def test_schedule_repository_delete_by_rp_not_found_returns_zero(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    assert repo.delete_by_route_passanger_id(uuid.uuid4()) == 0


def test_schedule_repository_delete_by_rp_does_not_touch_other_rps(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp_a, pickup_a = setup_rp(db_session)
    rp_b, pickup_b = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([make_schedule(rp_a.id, pickup_a.id, "monday")])
    repo.save_many([make_schedule(rp_b.id, pickup_b.id, "friday")])

    repo.delete_by_route_passanger_id(rp_a.id)

    assert repo.find_by_route_passanger_id(rp_a.id) == []
    remaining = repo.find_by_route_passanger_id(rp_b.id)
    assert len(remaining) == 1
    assert remaining[0].day_of_week == "friday"


# ---------------------------------------------------------------------------
# replace
# ---------------------------------------------------------------------------


def test_schedule_repository_replace_swaps_schedules(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp, pickup = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([
        make_schedule(rp.id, pickup.id, "monday"),
        make_schedule(rp.id, pickup.id, "tuesday"),
    ])

    new_items = [
        make_schedule(rp.id, pickup.id, "wednesday"),
        make_schedule(rp.id, pickup.id, "friday"),
    ]
    result = repo.replace(rp.id, new_items)

    assert len(result) == 2
    persisted = repo.find_by_route_passanger_id(rp.id)
    assert {s.day_of_week for s in persisted} == {"wednesday", "friday"}


def test_schedule_repository_replace_when_none_existed(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp, pickup = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)

    result = repo.replace(rp.id, [make_schedule(rp.id, pickup.id, "thursday")])

    assert len(result) == 1
    persisted = repo.find_by_route_passanger_id(rp.id)
    assert len(persisted) == 1
    assert persisted[0].day_of_week == "thursday"


def test_schedule_repository_replace_does_not_touch_other_rps(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_schedule_repository import (
        RoutePassangerScheduleRepositoryImpl,
    )

    rp_a, pickup_a = setup_rp(db_session)
    rp_b, pickup_b = setup_rp(db_session)
    repo = RoutePassangerScheduleRepositoryImpl(db_session)
    repo.save_many([make_schedule(rp_a.id, pickup_a.id, "monday")])
    repo.save_many([make_schedule(rp_b.id, pickup_b.id, "friday")])

    repo.replace(rp_a.id, [make_schedule(rp_a.id, pickup_a.id, "thursday")])

    remaining_b = repo.find_by_route_passanger_id(rp_b.id)
    assert len(remaining_b) == 1
    assert remaining_b[0].day_of_week == "friday"
