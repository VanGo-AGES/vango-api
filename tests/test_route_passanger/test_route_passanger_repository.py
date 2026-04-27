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


def make_route_passanger(
    session,
    route_id: uuid.UUID,
    user_id: uuid.UUID,
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


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_route_passanger_repository_save_returns_persisted_instance(db_session) -> None:
    """save deve retornar o RoutePassangerModel com id preenchido pelo banco."""
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    pickup = make_address(db_session, passenger.id, "Pickup")

    rp = RoutePassangerModel(
        route_id=route.id,
        user_id=passenger.id,
        status="pending",
        pickup_address_id=pickup.id,
    )

    repo = RoutePassangerRepositoryImpl(db_session)
    saved = repo.save(rp)

    assert saved is not None
    assert saved.id is not None


def test_route_passanger_repository_save_persists_correct_fields(db_session) -> None:
    """Os campos obrigatórios do vínculo devem ser persistidos corretamente."""
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    pickup = make_address(db_session, passenger.id, "Pickup")

    rp = RoutePassangerModel(
        route_id=route.id,
        user_id=passenger.id,
        status="pending",
        pickup_address_id=pickup.id,
    )

    repo = RoutePassangerRepositoryImpl(db_session)
    saved = repo.save(rp)

    assert saved.route_id == route.id
    assert saved.user_id == passenger.id
    assert saved.status == "pending"
    assert saved.pickup_address_id == pickup.id


def test_route_passanger_repository_save_is_queryable_after_save(db_session) -> None:
    """Após save, o vínculo deve ser encontrável via find_by_id."""
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    pickup = make_address(db_session, passenger.id, "Pickup")

    rp = RoutePassangerModel(
        route_id=route.id,
        user_id=passenger.id,
        status="pending",
        pickup_address_id=pickup.id,
    )

    repo = RoutePassangerRepositoryImpl(db_session)
    saved = repo.save(rp)

    db_session.expire_all()
    refetched = db_session.get(RoutePassangerModel, saved.id)
    assert refetched is not None
    assert refetched.user_id == passenger.id


def test_route_passanger_repository_save_with_dependent_id(db_session) -> None:
    """save deve persistir o dependent_id quando o vínculo é em nome de um dependente."""
    from src.domains.dependents.entity import DependentModel
    from src.domains.route_passangers.entity import RoutePassangerModel
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    guardian = make_user(db_session)
    dep = DependentModel(id=uuid.uuid4(), guardian_id=guardian.id, name="Filho")
    db_session.add(dep)
    db_session.flush()
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    pickup = make_address(db_session, guardian.id, "Pickup")

    rp = RoutePassangerModel(
        route_id=route.id,
        user_id=guardian.id,
        dependent_id=dep.id,
        status="pending",
        pickup_address_id=pickup.id,
    )

    repo = RoutePassangerRepositoryImpl(db_session)
    saved = repo.save(rp)

    assert saved.dependent_id == dep.id


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


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


def test_route_passanger_repository_find_by_id_not_found_returns_none(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.find_by_id(uuid.uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# find_by_route_and_status
# ---------------------------------------------------------------------------


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


def test_route_passanger_repository_find_by_route_empty_returns_empty_list(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_route_and_status(uuid.uuid4(), status="pending")
    assert results == []


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


def test_route_passanger_repository_update_status_not_found_returns_none(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.update_status(uuid.uuid4(), "accepted")
    assert result is None


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


def test_route_passanger_repository_count_accepted_zero_when_no_passangers(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    count = repo.count_accepted_by_route(uuid.uuid4())
    assert count == 0


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


def test_route_passanger_repository_delete_not_found_returns_false(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.delete(uuid.uuid4())
    assert result is False


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


# ===========================================================================
# US08 - TK03: find_active_by_user_and_route + find_by_user_and_route_id
# Arquivo: src/infrastructure/repositories/route_passanger_repository.py
# ===========================================================================


def make_dependent(session, guardian_id: uuid.UUID, name: str = "Dep"):
    from src.domains.dependents.entity import DependentModel

    dep = DependentModel(
        id=uuid.uuid4(),
        guardian_id=guardian_id,
        name=name,
    )
    session.add(dep)
    session.flush()
    return dep


# ---------------------------------------------------------------------------
# find_active_by_user_and_route
# ---------------------------------------------------------------------------


def test_rp_repository_find_active_returns_pending(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.find_active_by_user_and_route(passenger.id, None, route.id)

    assert result is not None
    assert result.id == rp.id


def test_rp_repository_find_active_returns_accepted(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp = make_route_passanger(db_session, route.id, passenger.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    result = repo.find_active_by_user_and_route(passenger.id, None, route.id)

    assert result is not None
    assert result.id == rp.id


def test_rp_repository_find_active_ignores_rejected(db_session) -> None:
    """rejected é considerado inativo — pode voltar a solicitar."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, passenger.id, status="rejected")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_by_user_and_route(passenger.id, None, route.id) is None


def test_rp_repository_find_active_ignores_removed(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, passenger.id, status="removed")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_by_user_and_route(passenger.id, None, route.id) is None


def test_rp_repository_find_active_not_found_returns_none(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_by_user_and_route(uuid.uuid4(), None, uuid.uuid4()) is None


def test_rp_repository_find_active_filters_by_dependent_id(db_session) -> None:
    """Dois RPs no mesmo par (user_id, route_id): um self, um para dependente.
    Buscar com dependent_id=None retorna o self; com dependent_id=X retorna o do dep."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    guardian = make_user(db_session, role="guardian")
    dep = make_dependent(db_session, guardian.id, "Filho")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    rp_self = make_route_passanger(db_session, route.id, guardian.id, status="accepted")
    rp_dep = make_route_passanger(db_session, route.id, guardian.id, status="pending", dependent_id=dep.id)

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_by_user_and_route(guardian.id, None, route.id).id == rp_self.id
    assert repo.find_active_by_user_and_route(guardian.id, dep.id, route.id).id == rp_dep.id


def test_rp_repository_find_active_filters_by_route(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    make_route_passanger(db_session, route_a.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_by_user_and_route(passenger.id, None, route_a.id) is not None
    assert repo.find_active_by_user_and_route(passenger.id, None, route_b.id) is None


# ---------------------------------------------------------------------------
# find_by_user_and_route_id
# ---------------------------------------------------------------------------


def test_rp_repository_find_by_user_and_route_returns_all_statuses(db_session) -> None:
    """Retorna todos os RPs daquele user na rota (inclui rejected/removed)."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, passenger.id, status="rejected")
    make_route_passanger(db_session, route.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_user_and_route_id(passenger.id, route.id)

    assert len(results) == 2
    assert {rp.status for rp in results} == {"rejected", "pending"}


def test_rp_repository_find_by_user_and_route_includes_dependents(db_session) -> None:
    """Guardian com RP self + RP de dependente na mesma rota: ambos retornam."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    guardian = make_user(db_session, role="guardian")
    dep = make_dependent(db_session, guardian.id)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, guardian.id, status="accepted")
    make_route_passanger(db_session, route.id, guardian.id, status="pending", dependent_id=dep.id)

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_by_user_and_route_id(guardian.id, route.id)
    assert len(results) == 2


def test_rp_repository_find_by_user_and_route_empty_returns_empty_list(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_by_user_and_route_id(uuid.uuid4(), uuid.uuid4()) == []


def test_rp_repository_find_by_user_and_route_filters_by_route(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    make_route_passanger(db_session, route_a.id, passenger.id, status="pending")
    make_route_passanger(db_session, route_b.id, passenger.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    assert len(repo.find_by_user_and_route_id(passenger.id, route_a.id)) == 1


# ===========================================================================
# US08 - TK13: find_active_with_route_by_user — home do passageiro
# Arquivo: src/infrastructure/repositories/route_passanger_repository.py
# ===========================================================================


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_returns_self_memberships(db_session) -> None:
    """Retorna RPs do próprio user com status pending/accepted."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    make_route_passanger(db_session, route_a.id, passenger.id, status="pending")
    make_route_passanger(db_session, route_b.id, passenger.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(passenger.id)

    assert len(results) == 2
    assert {rp.route_id for rp in results} == {route_a.id, route_b.id}


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_ignores_rejected_and_removed(db_session) -> None:
    """Não retorna rejected/removed — só pending/accepted."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    route_c = make_route(db_session, driver.id, origin.id, destination.id, invite_code="P3Q4R")
    make_route_passanger(db_session, route_a.id, passenger.id, status="rejected")
    make_route_passanger(db_session, route_b.id, passenger.id, status="removed")
    make_route_passanger(db_session, route_c.id, passenger.id, status="pending")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(passenger.id)

    assert len(results) == 1
    assert results[0].route_id == route_c.id


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_includes_dependents(db_session) -> None:
    """Retorna também vínculos ativos de dependentes do guardian."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    guardian = make_user(db_session, role="guardian")
    dep = make_dependent(db_session, guardian.id, "Filho")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")
    # guardian self em route_a
    make_route_passanger(db_session, route_a.id, guardian.id, status="accepted")
    # dep em route_b (user_id = guardian, dependent_id = dep)
    make_route_passanger(db_session, route_b.id, guardian.id, status="pending", dependent_id=dep.id)

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(guardian.id)

    assert len(results) == 2


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_empty_returns_empty_list(db_session) -> None:
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    repo = RoutePassangerRepositoryImpl(db_session)
    assert repo.find_active_with_route_by_user(uuid.uuid4()) == []


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_filters_by_user(db_session) -> None:
    """Não retorna vínculos de outros usuários."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    p1 = make_user(db_session, name="P1")
    p2 = make_user(db_session, name="P2")
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, p1.id, status="accepted")
    make_route_passanger(db_session, route.id, p2.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(p1.id)

    assert len(results) == 1
    assert results[0].user_id == p1.id


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_orders_by_joined_at_desc(db_session) -> None:
    """Resultados ordenados por joined_at desc — vínculo mais recente primeiro."""
    from datetime import datetime, timedelta, timezone

    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route_a = make_route(db_session, driver.id, origin.id, destination.id)
    route_b = make_route(db_session, driver.id, origin.id, destination.id, invite_code="X9Y8Z")

    older = make_route_passanger(db_session, route_a.id, passenger.id, status="accepted")
    newer = make_route_passanger(db_session, route_b.id, passenger.id, status="pending")

    older.joined_at = datetime.now(timezone.utc) - timedelta(days=2)
    newer.joined_at = datetime.now(timezone.utc)
    db_session.flush()

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(passenger.id)

    assert len(results) == 2
    assert results[0].id == newer.id
    assert results[1].id == older.id


@pytest.mark.skip(reason="US08-TK13")
def test_rp_repository_find_active_with_route_loads_route_relationship(db_session) -> None:
    """Os RPs retornados devem trazer o RouteModel acessível (eager load)."""
    from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

    driver = make_user(db_session, role="driver")
    passenger = make_user(db_session)
    origin = make_address(db_session, driver.id, "Casa")
    destination = make_address(db_session, driver.id, "PUCRS")
    route = make_route(db_session, driver.id, origin.id, destination.id)
    make_route_passanger(db_session, route.id, passenger.id, status="accepted")

    repo = RoutePassangerRepositoryImpl(db_session)
    results = repo.find_active_with_route_by_user(passenger.id)

    assert len(results) == 1
    assert results[0].route is not None
    assert results[0].route.id == route.id
