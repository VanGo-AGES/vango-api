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


@pytest.mark.skip(reason="US05-TK02")
def test_address_create_valid() -> None:
    from src.domains.routes.dtos import AddressCreate

    addr = AddressCreate(**make_address_payload())
    assert addr.label == "Casa"
    assert addr.zip == "91760-000"


@pytest.mark.skip(reason="US05-TK02")
def test_address_create_missing_required_fields() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(label="Casa")


@pytest.mark.skip(reason="US05-TK02")
def test_address_create_invalid_zip_format() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(**make_address_payload(zip="91760000"))


@pytest.mark.skip(reason="US05-TK02")
def test_address_create_state_must_be_two_chars() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import AddressCreate

    with pytest.raises(ValidationError):
        AddressCreate(**make_address_payload(state="Rio Grande do Sul"))


# --- RouteCreate ---


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_valid_outbound() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload())
    assert route.name == "PUCRS"
    assert route.route_type == "outbound"
    assert route.recurrence == "seg,ter,qua,qui,sex"


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_valid_inbound() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload(route_type="inbound"))
    assert route.route_type == "inbound"


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_invalid_route_type() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(route_type="ambos"))


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_missing_name() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    payload = make_route_payload()
    del payload["name"]
    with pytest.raises(ValidationError):
        RouteCreate(**payload)


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_empty_name() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(name=""))


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_recurrence_single_day() -> None:
    from src.domains.routes.dtos import RouteCreate

    route = RouteCreate(**make_route_payload(recurrence="sab"))
    assert route.recurrence == "sab"


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_recurrence_invalid_day() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence="mon,tue"))


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_recurrence_empty() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence=""))


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_recurrence_duplicate_days() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    with pytest.raises(ValidationError):
        RouteCreate(**make_route_payload(recurrence="seg,seg,ter"))


@pytest.mark.skip(reason="US05-TK02")
def test_route_create_missing_expected_time() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteCreate

    payload = make_route_payload()
    del payload["expected_time"]
    with pytest.raises(ValidationError):
        RouteCreate(**payload)
