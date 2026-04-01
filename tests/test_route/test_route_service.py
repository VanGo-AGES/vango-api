import uuid
from datetime import time
from unittest.mock import Mock, patch

import pytest

# ===========================================================================
# US05 - TK03: RouteService — create_route, _generate_invite_code,
#              regenerate_invite_code
# Arquivo:     src/domains/routes/service.py
# ===========================================================================


def make_route_create(**kwargs):
    from src.domains.routes.dtos import AddressCreate, RouteCreate

    origin = AddressCreate(
        label="Casa",
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    destination = AddressCreate(
        label="PUCRS",
        street="Av. Ipiranga",
        number="6681",
        neighborhood="Partenon",
        zip="90619-900",
        city="Porto Alegre",
        state="RS",
    )
    defaults = {
        "name": "PUCRS",
        "route_type": "outbound",
        "origin": origin,
        "destination": destination,
        "expected_time": time(8, 0),
        "recurrence": "seg,ter,qua,qui,sex",
    }
    defaults.update(kwargs)
    return RouteCreate(**defaults)


def make_vehicle_mock(capacity: int = 5):
    from src.domains.vehicles.entity import VehicleModel

    vehicle = Mock(spec=VehicleModel)
    vehicle.capacity = capacity
    return vehicle


def make_address_mock(label: str = "Casa"):
    from src.domains.addresses.entity import AddressModel

    address = Mock(spec=AddressModel)
    address.id = uuid.uuid4()
    address.label = label
    return address


def make_route_mock(driver_id: uuid.UUID = None):
    from src.domains.routes.entity import RouteModel

    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.driver_id = driver_id or uuid.uuid4()
    route.invite_code = "A1B2C"
    route.status = "inativa"
    return route


@pytest.mark.skip(reason="US05-TK03")
def test_create_route_success() -> None:
    """create_route deve salvar a rota com status inativa e invite_code gerado."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    vehicle = make_vehicle_mock(capacity=10)
    origin_address = make_address_mock("Casa")
    dest_address = make_address_mock("PUCRS")
    saved_route = make_route_mock(driver_id)

    route_repo = Mock()
    address_repo = Mock()
    vehicle_repo = Mock()

    vehicle_repo.get_by_driver_id.return_value = [vehicle]
    address_repo.save.side_effect = [origin_address, dest_address]
    route_repo.save.return_value = saved_route

    service = RouteService(route_repo, address_repo, vehicle_repo)
    result = service.create_route(driver_id, make_route_create())

    assert result == saved_route
    route_repo.save.assert_called_once()


@pytest.mark.skip(reason="US05-TK03")
def test_create_route_sets_status_inativa() -> None:
    """A rota deve ser salva com status='inativa'."""
    from src.domains.routes.entity import RouteModel
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    vehicle = make_vehicle_mock()
    origin_address = make_address_mock()
    dest_address = make_address_mock()

    route_repo = Mock()
    address_repo = Mock()
    vehicle_repo = Mock()

    vehicle_repo.get_by_driver_id.return_value = [vehicle]
    address_repo.save.side_effect = [origin_address, dest_address]
    route_repo.save.side_effect = lambda r: r

    service = RouteService(route_repo, address_repo, vehicle_repo)
    result = service.create_route(driver_id, make_route_create())

    assert result.status == "inativa"


@pytest.mark.skip(reason="US05-TK03")
def test_create_route_uses_vehicle_capacity_for_max_passengers() -> None:
    """max_passengers deve ser preenchido com a capacidade do veículo do motorista."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    vehicle = make_vehicle_mock(capacity=8)
    origin_address = make_address_mock()
    dest_address = make_address_mock()

    route_repo = Mock()
    address_repo = Mock()
    vehicle_repo = Mock()

    vehicle_repo.get_by_driver_id.return_value = [vehicle]
    address_repo.save.side_effect = [origin_address, dest_address]
    route_repo.save.side_effect = lambda r: r

    service = RouteService(route_repo, address_repo, vehicle_repo)
    result = service.create_route(driver_id, make_route_create())

    assert result.max_passengers == 8


@pytest.mark.skip(reason="US05-TK03")
def test_create_route_no_vehicle_raises_error() -> None:
    """Se o motorista não tem veículo, deve lançar NoVehicleError."""
    from src.domains.routes.errors import NoVehicleError
    from src.domains.routes.service import RouteService

    route_repo = Mock()
    address_repo = Mock()
    vehicle_repo = Mock()
    vehicle_repo.get_by_driver_id.return_value = []

    service = RouteService(route_repo, address_repo, vehicle_repo)
    with pytest.raises(NoVehicleError):
        service.create_route(uuid.uuid4(), make_route_create())


@pytest.mark.skip(reason="US05-TK03")
def test_create_route_generates_invite_code() -> None:
    """A rota deve ser criada com um invite_code alfanumérico de 5 caracteres."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    vehicle = make_vehicle_mock()
    origin_address = make_address_mock()
    dest_address = make_address_mock()

    route_repo = Mock()
    address_repo = Mock()
    vehicle_repo = Mock()

    vehicle_repo.get_by_driver_id.return_value = [vehicle]
    address_repo.save.side_effect = [origin_address, dest_address]
    route_repo.save.side_effect = lambda r: r

    service = RouteService(route_repo, address_repo, vehicle_repo)
    result = service.create_route(driver_id, make_route_create())

    assert len(result.invite_code) == 5
    assert result.invite_code.isalnum()


@pytest.mark.skip(reason="US05-TK03")
def test_generate_invite_code_returns_5_char_alphanumeric() -> None:
    """_generate_invite_code deve retornar string de 5 chars alfanuméricos maiúsculos."""
    from src.domains.routes.service import RouteService

    service = RouteService(Mock(), Mock(), Mock())
    code = service._generate_invite_code()

    assert len(code) == 5
    assert code.isalnum()
    assert code == code.upper()


@pytest.mark.skip(reason="US05-TK03")
def test_regenerate_invite_code_success() -> None:
    """regenerate_invite_code deve gerar novo código e atualizar a rota."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id)
    updated_route = make_route_mock(driver_id)
    updated_route.invite_code = "NEW99"

    route_repo = Mock()
    route_repo.find_by_id.return_value = route
    route_repo.update_invite_code.return_value = updated_route

    service = RouteService(route_repo, Mock(), Mock())
    result = service.regenerate_invite_code(route.id, driver_id)

    assert result.invite_code == "NEW99"
    route_repo.update_invite_code.assert_called_once()


@pytest.mark.skip(reason="US05-TK03")
def test_regenerate_invite_code_not_found_raises_error() -> None:
    """regenerate_invite_code deve lançar RouteNotFoundError se a rota não existir."""
    from src.domains.routes.errors import RouteNotFoundError
    from src.domains.routes.service import RouteService

    route_repo = Mock()
    route_repo.find_by_id.return_value = None

    service = RouteService(route_repo, Mock(), Mock())
    with pytest.raises(RouteNotFoundError):
        service.regenerate_invite_code(uuid.uuid4(), uuid.uuid4())


@pytest.mark.skip(reason="US05-TK03")
def test_regenerate_invite_code_wrong_owner_raises_error() -> None:
    """regenerate_invite_code deve lançar RouteOwnershipError se o motorista não for o dono."""
    from src.domains.routes.errors import RouteOwnershipError
    from src.domains.routes.service import RouteService

    owner_id = uuid.uuid4()
    other_driver_id = uuid.uuid4()
    route = make_route_mock(owner_id)

    route_repo = Mock()
    route_repo.find_by_id.return_value = route

    service = RouteService(route_repo, Mock(), Mock())
    with pytest.raises(RouteOwnershipError):
        service.regenerate_invite_code(route.id, other_driver_id)


# ===========================================================================
# US07 - TK03: RouteService — get_routes, get_route
# Arquivo:     src/domains/routes/service.py
# ===========================================================================


def test_get_routes_returns_all_driver_routes() -> None:
    """get_routes deve retornar todas as rotas do motorista."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    routes = [make_route_mock(driver_id), make_route_mock(driver_id)]

    route_repo = Mock()
    route_repo.find_all_by_driver_id.return_value = routes

    service = RouteService(route_repo, Mock(), Mock())
    result = service.get_routes(driver_id)

    assert len(result) == 2
    route_repo.find_all_by_driver_id.assert_called_once_with(driver_id)


def test_get_routes_empty_list() -> None:
    """get_routes deve retornar lista vazia se motorista não tem rotas."""
    from src.domains.routes.service import RouteService

    route_repo = Mock()
    route_repo.find_all_by_driver_id.return_value = []

    service = RouteService(route_repo, Mock(), Mock())
    result = service.get_routes(uuid.uuid4())

    assert result == []


def test_get_route_success() -> None:
    """get_route deve retornar a rota quando o motorista é o dono."""
    from src.domains.routes.service import RouteService

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id)

    route_repo = Mock()
    route_repo.find_by_id.return_value = route

    service = RouteService(route_repo, Mock(), Mock())
    result = service.get_route(route.id, driver_id)

    assert result == route


def test_get_route_not_found_raises_error() -> None:
    """get_route deve lançar RouteNotFoundError se a rota não existir."""
    from src.domains.routes.errors import RouteNotFoundError
    from src.domains.routes.service import RouteService

    route_repo = Mock()
    route_repo.find_by_id.return_value = None

    service = RouteService(route_repo, Mock(), Mock())
    with pytest.raises(RouteNotFoundError):
        service.get_route(uuid.uuid4(), uuid.uuid4())


def test_get_route_wrong_owner_raises_error() -> None:
    """get_route deve lançar RouteOwnershipError se o motorista não for o dono."""
    from src.domains.routes.errors import RouteOwnershipError
    from src.domains.routes.service import RouteService

    owner_id = uuid.uuid4()
    route = make_route_mock(owner_id)

    route_repo = Mock()
    route_repo.find_by_id.return_value = route

    service = RouteService(route_repo, Mock(), Mock())
    with pytest.raises(RouteOwnershipError):
        service.get_route(route.id, uuid.uuid4())
