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


# ===========================================================================
# US06 - TK01: RouteUpdate — atualização parcial de rota
# Arquivo:     src/domains/routes/dtos.py
# Critérios:   Todos os campos opcionais; valida route_type, recurrence,
#              e origin != destination quando ambos presentes.
# ===========================================================================


def test_route_update_all_fields_optional() -> None:
    from src.domains.routes.dtos import RouteUpdate

    update = RouteUpdate()
    assert update.name is None
    assert update.recurrence is None
    assert update.origin is None
    assert update.destination is None


def test_route_update_partial_only_name() -> None:
    from src.domains.routes.dtos import RouteUpdate

    update = RouteUpdate(name="Nova Rota")
    assert update.name == "Nova Rota"
    assert update.route_type is None


def test_route_update_partial_only_recurrence() -> None:
    from src.domains.routes.dtos import RouteUpdate

    update = RouteUpdate(recurrence="seg,ter")
    assert update.recurrence == "seg,ter"


def test_route_update_invalid_route_type() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteUpdate

    with pytest.raises(ValidationError):
        RouteUpdate(route_type="ambos")


def test_route_update_invalid_recurrence_day() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteUpdate

    with pytest.raises(ValidationError):
        RouteUpdate(recurrence="mon,tue")


def test_route_update_recurrence_duplicate_days() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteUpdate

    with pytest.raises(ValidationError):
        RouteUpdate(recurrence="seg,seg,ter")


def test_route_update_origin_and_destination_cannot_be_equal() -> None:
    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteUpdate

    same = make_address_payload()
    with pytest.raises(ValidationError):
        RouteUpdate(origin=same, destination=same)


def test_route_update_accepts_only_origin_without_destination() -> None:
    from src.domains.routes.dtos import RouteUpdate

    update = RouteUpdate(origin=make_address_payload())
    assert update.origin is not None
    assert update.destination is None


def test_route_update_expected_time_valid() -> None:
    from datetime import time

    from src.domains.routes.dtos import RouteUpdate

    update = RouteUpdate(expected_time="09:30:00")
    assert update.expected_time == time(9, 30)


# ===========================================================================
# US08 - TK01: RouteInviteSummaryResponse — resumo da rota para o passageiro
# Arquivo: src/domains/routes/dtos.py
# Critérios:
#   Fields: id (UUID), name (str), route_type (str), recurrence (str),
#           expected_time (time), max_passengers (int), accepted_count (int),
#           origin_address (AddressResponse), destination_address (AddressResponse)
#   Não expõe: invite_code, passageiros, stops, status
# ===========================================================================


def test_route_invite_summary_response_accepts_valid_payload() -> None:
    from datetime import time
    from uuid import uuid4

    from src.domains.routes.dtos import RouteInviteSummaryResponse

    payload = {
        "id": uuid4(),
        "name": "PUCRS",
        "route_type": "outbound",
        "recurrence": "seg,ter,qua",
        "expected_time": time(8, 0),
        "max_passengers": 5,
        "accepted_count": 2,
        "origin_address": {
            "id": uuid4(),
            "label": "Casa",
            "street": "Av. Coronel Marcos",
            "number": "861",
            "neighborhood": "Três Figueiras",
            "zip": "91760-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "destination_address": {
            "id": uuid4(),
            "label": "PUCRS",
            "street": "Av. Ipiranga",
            "number": "6681",
            "neighborhood": "Partenon",
            "zip": "90619-900",
            "city": "Porto Alegre",
            "state": "RS",
        },
    }
    response = RouteInviteSummaryResponse(**payload)
    assert response.name == "PUCRS"
    assert response.max_passengers == 5
    assert response.accepted_count == 2


def test_route_invite_summary_response_does_not_expose_invite_code() -> None:
    from src.domains.routes.dtos import RouteInviteSummaryResponse

    assert "invite_code" not in RouteInviteSummaryResponse.model_fields


def test_route_invite_summary_response_does_not_expose_status() -> None:
    from src.domains.routes.dtos import RouteInviteSummaryResponse

    assert "status" not in RouteInviteSummaryResponse.model_fields


def test_route_invite_summary_response_does_not_expose_stops() -> None:
    from src.domains.routes.dtos import RouteInviteSummaryResponse

    assert "stops" not in RouteInviteSummaryResponse.model_fields


def test_route_invite_summary_response_requires_accepted_count() -> None:
    from datetime import time
    from uuid import uuid4

    from pydantic import ValidationError

    from src.domains.routes.dtos import RouteInviteSummaryResponse

    payload = {
        "id": uuid4(),
        "name": "PUCRS",
        "route_type": "outbound",
        "recurrence": "seg",
        "expected_time": time(8, 0),
        "max_passengers": 5,
        "origin_address": {
            "id": uuid4(), "label": "o", "street": "o", "number": "1",
            "neighborhood": "o", "zip": "12345-000", "city": "o", "state": "RS",
        },
        "destination_address": {
            "id": uuid4(), "label": "d", "street": "d", "number": "1",
            "neighborhood": "d", "zip": "12345-000", "city": "d", "state": "RS",
        },
    }
    with pytest.raises(ValidationError):
        RouteInviteSummaryResponse(**payload)
