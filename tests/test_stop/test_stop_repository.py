"""US07 — Tests de StopRepositoryImpl (integração SQLite)."""

import uuid

from src.domains.addresses.entity import AddressModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.routes.entity import RouteModel
from src.domains.stops.entity import StopModel
from src.domains.users.entity import UserModel
from src.infrastructure.repositories.stop_repository import StopRepositoryImpl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_driver(db_session) -> UserModel:
    driver = UserModel(
        name="Motorista",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    return driver


def make_passenger(db_session) -> UserModel:
    user = UserModel(
        name="Passageiro",
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="11988888888",
        password_hash="hashed",
        role="passanger",
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_address(db_session, user_id, label: str = "Casa") -> AddressModel:
    addr = AddressModel(
        user_id=user_id,
        label=label,
        street="Rua X",
        number="100",
        neighborhood="Centro",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add(addr)
    db_session.flush()
    return addr


def make_route(db_session, driver_id, origin_id, destination_id) -> RouteModel:
    from datetime import time

    route = RouteModel(
        driver_id=driver_id,
        origin_address_id=origin_id,
        destination_address_id=destination_id,
        name="Rota 1",
        recurrence="seg,ter,qua",
        max_passengers=4,
        expected_time=time(8, 0),
        status="inativa",
        invite_code=f"CODE{str(uuid.uuid4())[:3]}",
        route_type="outbound",
    )
    db_session.add(route)
    db_session.flush()
    return route


def make_rp(
    db_session,
    route_id,
    user_id,
    pickup_address_id,
    status: str = "accepted",
) -> RoutePassangerModel:
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=user_id,
        status=status,
        pickup_address_id=pickup_address_id,
    )
    db_session.add(rp)
    db_session.flush()
    return rp


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_stop_repository_save_persists(db_session) -> None:
    """save deve persistir a stop no banco e retornar o objeto com id."""
    driver = make_driver(db_session)
    passenger = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    pickup = make_address(db_session, passenger.id, "Parada Passageiro")
    rp = make_rp(db_session, route.id, passenger.id, pickup_address_id=pickup.id)
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    stop = StopModel(
        route_id=route.id,
        route_passanger_id=rp.id,
        address_id=pickup.id,
        order_index=1,
        type="embarque",
    )
    saved = repo.save(stop)

    assert saved.id is not None
    assert saved.route_id == route.id
    assert saved.route_passanger_id == rp.id
    assert saved.address_id == pickup.id
    assert saved.order_index == 1
    assert saved.type == "embarque"


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


def test_stop_repository_find_by_id_returns_stop(db_session) -> None:
    driver = make_driver(db_session)
    passenger = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    pickup = make_address(db_session, passenger.id, "Parada")
    rp = make_rp(db_session, route.id, passenger.id, pickup_address_id=pickup.id)

    repo = StopRepositoryImpl(db_session)
    stop = repo.save(StopModel(route_id=route.id, route_passanger_id=rp.id, address_id=pickup.id, order_index=1, type="embarque"))

    found = repo.find_by_id(stop.id)

    assert found is not None
    assert found.id == stop.id
    assert found.route_id == route.id


def test_stop_repository_find_by_id_missing_returns_none(db_session) -> None:
    repo = StopRepositoryImpl(db_session)
    assert repo.find_by_id(uuid.uuid4()) is None


# ---------------------------------------------------------------------------
# find_by_route_id
# ---------------------------------------------------------------------------


def test_stop_repository_find_by_route_id_returns_all_stops(db_session) -> None:
    """find_by_route_id deve retornar todas as stops da rota."""
    driver = make_driver(db_session)
    p1 = make_passenger(db_session)
    p2 = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    addr1 = make_address(db_session, p1.id, "Parada 1")
    addr2 = make_address(db_session, p2.id, "Parada 2")
    rp1 = make_rp(db_session, route.id, p1.id, pickup_address_id=addr1.id)
    rp2 = make_rp(db_session, route.id, p2.id, pickup_address_id=addr2.id)
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp1.id, address_id=addr1.id, order_index=1, type="embarque"))
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp2.id, address_id=addr2.id, order_index=2, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    stops = repo.find_by_route_id(route.id)

    assert len(stops) == 2


def test_stop_repository_find_by_route_id_empty(db_session) -> None:
    """find_by_route_id deve retornar [] se rota não tem stops."""
    repo = StopRepositoryImpl(db_session)
    stops = repo.find_by_route_id(uuid.uuid4())

    assert stops == []


def test_stop_repository_find_by_route_id_filters_by_route(db_session) -> None:
    """find_by_route_id deve retornar apenas stops da rota informada."""
    driver = make_driver(db_session)
    pa = make_passenger(db_session)
    pb = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, dest.id)
    route_b = make_route(db_session, driver.id, origin.id, dest.id)
    addr_a = make_address(db_session, pa.id, "Parada A")
    addr_b = make_address(db_session, pb.id, "Parada B")
    rp_a = make_rp(db_session, route_a.id, pa.id, pickup_address_id=addr_a.id)
    rp_b = make_rp(db_session, route_b.id, pb.id, pickup_address_id=addr_b.id)
    db_session.add(StopModel(route_id=route_a.id, route_passanger_id=rp_a.id, address_id=addr_a.id, order_index=1, type="embarque"))
    db_session.add(StopModel(route_id=route_b.id, route_passanger_id=rp_b.id, address_id=addr_b.id, order_index=1, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    stops = repo.find_by_route_id(route_a.id)

    assert len(stops) == 1
    assert stops[0].route_id == route_a.id


def test_stop_repository_find_by_route_id_orders_by_order_index(db_session) -> None:
    """find_by_route_id deve retornar as stops ordenadas por order_index."""
    driver = make_driver(db_session)
    p1 = make_passenger(db_session)
    p2 = make_passenger(db_session)
    p3 = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    a1 = make_address(db_session, p1.id, "A1")
    a2 = make_address(db_session, p2.id, "A2")
    a3 = make_address(db_session, p3.id, "A3")
    rp1 = make_rp(db_session, route.id, p1.id, pickup_address_id=a1.id)
    rp2 = make_rp(db_session, route.id, p2.id, pickup_address_id=a2.id)
    rp3 = make_rp(db_session, route.id, p3.id, pickup_address_id=a3.id)
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp1.id, address_id=a1.id, order_index=3, type="embarque"))
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp2.id, address_id=a2.id, order_index=1, type="embarque"))
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp3.id, address_id=a3.id, order_index=2, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    stops = repo.find_by_route_id(route.id)

    assert [s.order_index for s in stops] == [1, 2, 3]


# ---------------------------------------------------------------------------
# find_by_route_passanger_id
# ---------------------------------------------------------------------------


def test_stop_repository_find_by_route_passanger_id_returns_stop(db_session) -> None:
    """find_by_route_passanger_id deve retornar a stop associada ao rp."""
    driver = make_driver(db_session)
    passenger = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    pickup = make_address(db_session, passenger.id, "Parada")
    rp = make_rp(db_session, route.id, passenger.id, pickup_address_id=pickup.id)
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp.id, address_id=pickup.id, order_index=1, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    found = repo.find_by_route_passanger_id(rp.id)

    assert found is not None
    assert found.route_passanger_id == rp.id


def test_stop_repository_find_by_route_passanger_id_not_found_returns_none(db_session) -> None:
    """find_by_route_passanger_id deve retornar None se não houver stop."""
    repo = StopRepositoryImpl(db_session)
    found = repo.find_by_route_passanger_id(uuid.uuid4())

    assert found is None


# ---------------------------------------------------------------------------
# delete_by_route_passanger_id
# ---------------------------------------------------------------------------


def test_stop_repository_delete_by_route_passanger_id_removes_stop(db_session) -> None:
    """delete_by_route_passanger_id deve remover a stop e retornar True."""
    driver = make_driver(db_session)
    passenger = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    pickup = make_address(db_session, passenger.id, "Parada")
    rp = make_rp(db_session, route.id, passenger.id, pickup_address_id=pickup.id)
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp.id, address_id=pickup.id, order_index=1, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    deleted = repo.delete_by_route_passanger_id(rp.id)

    assert deleted is True
    assert db_session.query(StopModel).filter(StopModel.route_passanger_id == rp.id).first() is None


def test_stop_repository_delete_by_route_passanger_id_not_found_returns_false(db_session) -> None:
    """delete_by_route_passanger_id deve retornar False se não houver stop."""
    repo = StopRepositoryImpl(db_session)
    deleted = repo.delete_by_route_passanger_id(uuid.uuid4())

    assert deleted is False


def test_stop_repository_delete_by_route_passanger_id_preserves_other_stops(db_session) -> None:
    """delete_by_route_passanger_id deve remover apenas a stop do rp informado."""
    driver = make_driver(db_session)
    p1 = make_passenger(db_session)
    p2 = make_passenger(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    dest = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, dest.id)
    addr1 = make_address(db_session, p1.id, "Parada 1")
    addr2 = make_address(db_session, p2.id, "Parada 2")
    rp1 = make_rp(db_session, route.id, p1.id, pickup_address_id=addr1.id)
    rp2 = make_rp(db_session, route.id, p2.id, pickup_address_id=addr2.id)
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp1.id, address_id=addr1.id, order_index=1, type="embarque"))
    db_session.add(StopModel(route_id=route.id, route_passanger_id=rp2.id, address_id=addr2.id, order_index=2, type="embarque"))
    db_session.commit()

    repo = StopRepositoryImpl(db_session)
    repo.delete_by_route_passanger_id(rp1.id)

    remaining = db_session.query(StopModel).all()
    assert len(remaining) == 1
    assert remaining[0].route_passanger_id == rp2.id
