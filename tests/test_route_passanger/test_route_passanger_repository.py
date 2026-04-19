import uuid
from datetime import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database import Base

# ===========================================================================
# US06 - TK06: RoutePassangerRepository — persistência/queries básicas
# Arquivo:     src/infrastructure/repositories/route_passanger_repository.py
# Métodos:     find_by_id, find_by_route_and_status, update_status,
#              count_accepted_by_route, delete
# ===========================================================================


# ---------------------------------------------------------------------------
# Fixtures
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


def make_route(session, driver_id: uuid.UUID, origin_id: uuid.UUID, destination_id: uuid.UUID, **kwargs):
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
        "invite_code": "A1B2C",
    }
    defaults.update(kwargs)
    route = RouteModel(**defaults)
    session.add(route)
    session.flush()
    return route


def make_route_passanger(session, route_id: uuid.UUID, user_id: uuid.UUID, status: str = "pending", dependent_id=None):
    from src.domains.route_passangers.entity import RoutePassangerModel

    rp = RoutePassangerModel(
        id=uuid.uuid4(),
        route_id=route_id,
        user_id=user_id,
        dependent_id=dependent_id,
        status=status,
    )
    session.add(rp)
    session.flush()
    return rp


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_id_returns_model(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver", name="Driver")
    passenger = make_user(db_session, role="guardian", name="Passenger")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id)

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.find_by_id(rp.id)

    assert result is not None
    assert result.id == rp.id
    assert result.route_id == route.id


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_id_not_found_returns_none(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.find_by_id(uuid.uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# find_by_route_and_status
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_route_filters_by_status(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    p3 = make_user(db_session, name="P3")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="pending")
    make_route_passanger(db_session, route.id, p2.id, status="pending")
    make_route_passanger(db_session, route.id, p3.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(route.id, status="pending")

    assert len(results) == 2
    assert all(rp.status == "pending" for rp in results)


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_route_no_status_returns_all(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="pending")
    make_route_passanger(db_session, route.id, p2.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(route.id, status=None)

    assert len(results) == 2


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_route_empty_returns_empty_list(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(uuid.uuid4(), status="pending")
    assert results == []


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_route_filters_out_other_statuses(db_session) -> None:
    """Quando status='accepted', não retorna rejected/removed da mesma rota."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    p3 = make_user(db_session, name="P3")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="accepted")
    make_route_passanger(db_session, route.id, p2.id, status="rejected")
    make_route_passanger(db_session, route.id, p3.id, status="removed")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(route.id, status="accepted")

    assert len(results) == 1
    assert results[0].user_id == p1.id


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_find_by_route_filters_by_route_id(db_session) -> None:
    """Não retorna passageiros de outras rotas."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    make_route_passanger(db_session, route_a.id, p1.id, status="pending")
    make_route_passanger(db_session, route_b.id, p2.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(route_a.id, status="pending")

    assert len(results) == 1
    assert results[0].user_id == p1.id


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_update_status_accepted(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    updated = repo.update_status(rp.id, "accepted")

    assert updated is not None
    assert updated.status == "accepted"


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_update_status_rejected(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    updated = repo.update_status(rp.id, "rejected")

    assert updated is not None
    assert updated.status == "rejected"


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_update_status_not_found_returns_none(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.update_status(uuid.uuid4(), "accepted")
    assert result is None


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_update_status_persists_in_db(db_session) -> None:
    """Após update_status, um novo find_by_id deve refletir o novo status."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    repo.update_status(rp.id, "accepted")

    refetched = repo.find_by_id(rp.id)
    assert refetched is not None
    assert refetched.status == "accepted"


# ---------------------------------------------------------------------------
# count_accepted_by_route
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_count_accepted_only(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    p3 = make_user(db_session, name="P3")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="accepted")
    make_route_passanger(db_session, route.id, p2.id, status="accepted")
    make_route_passanger(db_session, route.id, p3.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    count = repo.count_accepted_by_route(route.id)

    assert count == 2


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_count_accepted_zero_when_no_passangers(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    count = repo.count_accepted_by_route(uuid.uuid4())
    assert count == 0


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_count_accepted_filters_by_route(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    make_route_passanger(db_session, route_a.id, p1.id, status="accepted")
    make_route_passanger(db_session, route_b.id, p2.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.count_accepted_by_route(route_a.id) == 1


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_count_accepted_ignores_other_statuses(db_session) -> None:
    """count_accepted_by_route só conta status='accepted', ignora pending/rejected/removed."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    p3 = make_user(db_session, name="P3")
    p4 = make_user(db_session, name="P4")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="accepted")
    make_route_passanger(db_session, route.id, p2.id, status="pending")
    make_route_passanger(db_session, route.id, p3.id, status="rejected")
    make_route_passanger(db_session, route.id, p4.id, status="removed")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.count_accepted_by_route(route.id) == 1


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_delete_returns_true(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.delete(rp.id)

    assert result is True
    assert repo.find_by_id(rp.id) is None


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_delete_not_found_returns_false(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.delete(uuid.uuid4())
    assert result is False


@pytest.mark.skip(reason="US06-TK06")
def test_route_passanger_repository_delete_only_removes_target(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp1 = make_route_passanger(db_session, route.id, p1.id, status="accepted")
    rp2 = make_route_passanger(db_session, route.id, p2.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    repo.delete(rp1.id)

    assert repo.find_by_id(rp1.id) is None
    assert repo.find_by_id(rp2.id) is not None
