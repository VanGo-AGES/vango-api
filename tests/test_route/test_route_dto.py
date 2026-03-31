import pytest

# ===========================================================================
# US05 - TK02: Contratos de criação e resposta de rota
# Arquivo:     src/domains/routes/dtos.py
# Critérios:   RouteCreate valida campos obrigatórios, route_type e recurrence
#              AddressCreate valida CEP e campos obrigatórios
#              RouteResponse expõe endereços aninhados e invite_code
# ===========================================================================


def make_address_payload(**kwargs) -> dict:
    defaults = {
        "label": "Casa",
        "street": "Av. Coronel Marcos",
        "number": "861",
        "neighborhood": "Três Figueiras",
        "zip": "91760-000",
        "city": "Porto Alegre",
        "state": "RS",
    }
    defaults.update(kwargs)
    return defaults


def make_route_payload(**kwargs) -> dict:
    defaults = {
        "name": "PUCRS",
        "route_type": "outbound",
        "origin": make_address_payload(label="Casa"),
        "destination": make_address_payload(label="PUCRS", street="Av. Ipiranga", number="6681", zip="90619-900"),
        "expected_time": "08:00:00",
        "recurrence": "seg,ter,qua,qui,sex",
    }
    defaults.update(kwargs)
    return defaults


# --- AddressCreate ---


def test_address_create_valid() -> None:
    from src.domains.routes.dtos import AddressCreate

    addr = AddressCreate(**make_address_payload())
    assert addr.label == "Casa"
    assert addr.zip == "91760-000"


def test_address_create_missing_required_fields() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(label="Casa")


def test_address_create_invalid_zip_format() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(**make_address_payload(zip="91760000"))


def test_address_create_state_must_be_two_chars() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(**make_address_payload(state="Rio Grande do Sul"))


def test_address_create_state_is_normalized_to_uppercase() -> None:
    from src.domains.routes.dtos import AddressCreate

    addr = AddressCreate(**make_address_payload(state="rs"))
    assert addr.state == "RS"


def test_address_create_state_lowercase_is_accepted_and_uppercased() -> None:
    from src.domains.routes.dtos import AddressCreate

    addr = AddressCreate(**make_address_payload(state="sp"))
    assert addr.state == "SP"


# --- RouteCreate ---


def test_route_create_valid_outbound() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload())
    assert route.name == "PUCRS"
    assert route.route_type == "outbound"
    assert route.recurrence == "seg,ter,qua,qui,sex"


def test_route_create_valid_inbound() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload(route_type="inbound"))
    assert route.route_type == "inbound"


def test_route_create_invalid_route_type() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(route_type="ambos"))


def test_route_create_missing_name() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    payload = make_route_payload()
    del payload["name"]
    with pytest.raises(ValidationError):
        RouteCreate(**payload)


def test_route_create_empty_name() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(name=""))


def test_route_create_recurrence_single_day() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload(recurrence="sab"))
    assert route.recurrence == "sab"


def test_route_create_recurrence_invalid_day() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence="mon,tue"))


def test_route_create_recurrence_empty() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence=""))


def test_route_create_recurrence_duplicate_days() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence="seg,seg,ter"))


def test_route_create_missing_expected_time() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    payload = make_route_payload()
    del payload["expected_time"]
    with pytest.raises(ValidationError):
        RouteCreate(**payload)


# --- RouteCreate: origin != destination ---


def test_route_create_origin_and_destination_cannot_be_equal() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    same_address = make_address_payload()
    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(origin=same_address, destination=same_address))


def test_route_create_different_origin_and_destination_is_valid() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload())
    assert route.origin.street != route.destination.street
