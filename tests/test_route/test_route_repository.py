import uuid
from datetime import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database import Base

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


def make_driver(session):
    from src.domains.users.entity import UserModel

    driver = UserModel(
        id=uuid.uuid4(),
        name="João Motorista",
        email=f"driver_{uuid.uuid4().hex[:6]}@test.com",
        phone="54999999999",
        password_hash="hashed",
        role="driver",
    )
    session.add(driver)
    session.flush()
    return driver


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


# ===========================================================================
# US05 - TK01: AddressRepository e RouteRepository — persistência básica
# Arquivo:     src/infrastructure/repositories/address_repository.py
#              src/infrastructure/repositories/route_repository.py
# ===========================================================================


def test_address_repository_save_returns_address_with_id(db_session) -> None:
    from src.domains.addresses.entity import AddressModel
    from src.infrastructure.repositories.address_repository import AddressRepositoryImpl

    driver = make_driver(db_session)
    repo = AddressRepositoryImpl(db_session)
    address = AddressModel(
        id=uuid.uuid4(),
        user_id=driver.id,
        label="Casa",
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    saved = repo.save(address)
    assert saved.id is not None
    assert saved.label == "Casa"


def test_address_repository_save_persists_in_database(db_session) -> None:
    from src.domains.addresses.entity import AddressModel
    from src.infrastructure.repositories.address_repository import AddressRepositoryImpl

    driver = make_driver(db_session)
    repo = AddressRepositoryImpl(db_session)
    address = AddressModel(
        id=uuid.uuid4(),
        user_id=driver.id,
        label="Escola",
        street="Av. Ipiranga",
        number="6681",
        neighborhood="Partenon",
        zip="90619-900",
        city="Porto Alegre",
        state="RS",
    )
    repo.save(address)
    found = db_session.query(AddressModel).filter_by(label="Escola").first()
    assert found is not None


def test_address_repository_save_without_lat_lng(db_session) -> None:
    """latitude e longitude são opcionais — devem aceitar None."""
    from src.domains.addresses.entity import AddressModel
    from src.infrastructure.repositories.address_repository import AddressRepositoryImpl

    driver = make_driver(db_session)
    repo = AddressRepositoryImpl(db_session)
    address = AddressModel(
        id=uuid.uuid4(),
        user_id=driver.id,
        label="Sem coordenadas",
        street="Rua X",
        number="1",
        neighborhood="Centro",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
        latitude=None,
        longitude=None,
    )
    saved = repo.save(address)
    assert saved.latitude is None
    assert saved.longitude is None


def test_route_repository_save_returns_route_with_id(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver = make_driver(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    repo = RouteRepositoryImpl(db_session)
    route = make_route(db_session, driver.id, origin.id, destination.id)
    saved = repo.save(route)
    assert saved.id is not None
    assert saved.name == "PUCRS"
    assert saved.status == "inativa"


def test_route_repository_save_persists_invite_code(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver = make_driver(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    repo = RouteRepositoryImpl(db_session)
    route = make_route(db_session, driver.id, origin.id, destination.id, invite_code="XYZ99")
    saved = repo.save(route)
    assert saved.invite_code == "XYZ99"


def test_route_repository_find_by_id_returns_route(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver = make_driver(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    db_session.commit()

    repo = RouteRepositoryImpl(db_session)
    found = repo.find_by_id(route.id)
    assert found is not None
    assert found.id == route.id


def test_route_repository_find_by_id_not_found(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    repo = RouteRepositoryImpl(db_session)
    result = repo.find_by_id(uuid.uuid4())
    assert result is None


def test_route_repository_update_invite_code(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver = make_driver(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id, invite_code="OLD00")
    db_session.commit()

    repo = RouteRepositoryImpl(db_session)
    updated = repo.update_invite_code(route.id, "NEW99")
    assert updated is not None
    assert updated.invite_code == "NEW99"


def test_route_repository_update_invite_code_not_found(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    repo = RouteRepositoryImpl(db_session)
    result = repo.update_invite_code(uuid.uuid4(), "XXXXX")
    assert result is None


# ===========================================================================
# US07 - TK01: RouteRepository — listagem por motorista
# Arquivo:     src/infrastructure/repositories/route_repository.py
# ===========================================================================


def test_route_repository_find_all_by_driver_id_returns_list(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver = make_driver(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    make_route(db_session, driver.id, origin.id, destination.id, invite_code="AAA11")
    make_route(db_session, driver.id, origin.id, destination.id, invite_code="BBB22", name="Escola")
    db_session.commit()

    repo = RouteRepositoryImpl(db_session)
    routes = repo.find_all_by_driver_id(driver.id)
    assert len(routes) == 2


def test_route_repository_find_all_by_driver_id_empty(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    repo = RouteRepositoryImpl(db_session)
    routes = repo.find_all_by_driver_id(uuid.uuid4())
    assert routes == []


def test_route_repository_find_all_by_driver_id_only_own(db_session) -> None:
    from src.infrastructure.repositories.route_repository import RouteRepositoryImpl

    driver_a = make_driver(db_session)
    driver_b = make_driver(db_session)
    origin_a = make_address(db_session, driver_a.id, "Casa A")
    dest_a = make_address(db_session, driver_a.id, "PUCRS")
    origin_b = make_address(db_session, driver_b.id, "Casa B")
    dest_b = make_address(db_session, driver_b.id, "PUCRS")
    make_route(db_session, driver_a.id, origin_a.id, dest_a.id, invite_code="AAA11")
    make_route(db_session, driver_b.id, origin_b.id, dest_b.id, invite_code="BBB22")
    db_session.commit()

    repo = RouteRepositoryImpl(db_session)
    routes = repo.find_all_by_driver_id(driver_a.id)
    assert len(routes) == 1
    assert routes[0].driver_id == driver_a.id
