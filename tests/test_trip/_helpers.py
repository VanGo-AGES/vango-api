"""Helpers compartilhados pelos testes de integração do domínio trips (US09).

Cria usuários, veículos, rotas e vínculos route_passanger numa sessão SQLite
em memória, para testes de repositório e controller de integração.
"""

import uuid
from datetime import datetime, time, timezone

from src.domains.addresses.entity import AddressModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.routes.entity import RouteModel
from src.domains.stops.entity import StopModel
from src.domains.trips.entity import AbsenceModel, TripModel, TripPassangerModel
from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel


def make_driver(db_session, name: str = "Motorista") -> UserModel:
    driver = UserModel(
        name=name,
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="51999990000",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    return driver


def make_passenger(db_session, name: str = "Passageiro") -> UserModel:
    user = UserModel(
        name=name,
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="51988887777",
        password_hash="hashed",
        role="guardian",
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_vehicle(db_session, driver_id, capacity: int = 4) -> VehicleModel:
    vehicle = VehicleModel(
        driver_id=driver_id,
        plate=f"RIT{str(uuid.uuid4())[:4].upper()}",
        capacity=capacity,
    )
    db_session.add(vehicle)
    db_session.flush()
    return vehicle


def make_address(db_session, user_id, label: str = "Endereço") -> AddressModel:
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


def make_route(db_session, driver_id, status: str = "ativa") -> RouteModel:
    origin = make_address(db_session, driver_id, "Casa")
    destination = make_address(db_session, driver_id, "PUCRS")
    route = RouteModel(
        driver_id=driver_id,
        origin_address_id=origin.id,
        destination_address_id=destination.id,
        name="PUCRS Manhã",
        recurrence="seg,ter,qua,qui,sex",
        max_passengers=4,
        expected_time=time(8, 0),
        status=status,
        invite_code=f"IT{str(uuid.uuid4())[:3].upper()}",
        route_type="outbound",
    )
    db_session.add(route)
    db_session.flush()
    return route


def make_rp(
    db_session,
    route_id,
    user_id,
    status: str = "accepted",
) -> RoutePassangerModel:
    pickup = make_address(db_session, user_id, "Casa Passageiro")
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=user_id,
        status=status,
        pickup_address_id=pickup.id,
    )
    db_session.add(rp)
    db_session.flush()
    return rp


def make_stop(db_session, route_id, route_passanger_id, address_id, order_index: int = 1) -> StopModel:
    stop = StopModel(
        route_id=route_id,
        route_passanger_id=route_passanger_id,
        address_id=address_id,
        order_index=order_index,
        type="embarque",
    )
    db_session.add(stop)
    db_session.flush()
    return stop


def make_trip(
    db_session,
    route_id,
    vehicle_id,
    status: str = "iniciada",
    trip_date: datetime | None = None,
) -> TripModel:
    now = trip_date or datetime.now(timezone.utc)
    trip = TripModel(
        route_id=route_id,
        vehicle_id=vehicle_id,
        trip_date=now,
        status=status,
        started_at=now if status != "cancelada" else None,
    )
    db_session.add(trip)
    db_session.flush()
    return trip


def make_trip_passanger(
    db_session,
    trip_id,
    route_passanger_id,
    status: str = "pendente",
) -> TripPassangerModel:
    tp = TripPassangerModel(
        trip_id=trip_id,
        route_passanger_id=route_passanger_id,
        status=status,
    )
    db_session.add(tp)
    db_session.flush()
    return tp


def make_absence(
    db_session,
    route_passanger_id,
    absence_date: datetime,
    trip_id=None,
    reason: str | None = None,
) -> AbsenceModel:
    absence = AbsenceModel(
        trip_id=trip_id,
        route_passanger_id=route_passanger_id,
        absence_date=absence_date,
        reason=reason,
    )
    db_session.add(absence)
    db_session.flush()
    return absence
