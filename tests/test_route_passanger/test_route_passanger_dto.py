import pytest

# ===========================================================================
# US06 - TK05: RoutePassangerResponse + Erros do domínio route_passangers
# Arquivos:    src/domains/route_passangers/dtos.py
#              src/domains/route_passangers/errors.py
# Critérios:
#   DTO RoutePassangerResponse expõe:
#     obrigatórios: id, route_id, status, requested_at, user_id, user_name,
#                   user_phone, pickup_address_id
#     opcionais (default None): joined_at, dependent_id, dependent_name,
#                                guardian_name
#     model_config deve permitir construção a partir de objetos ORM
#     (from_attributes=True).
#   Erros: RoutePassangerNotFoundError, RouteCapacityExceededError,
#          RoutePassangerAlreadyProcessedError — todos herdam de Exception
#          e possuem mensagem default em pt-BR.
#
#   Observação: user_phone corresponde a user.phone no UserModel (não-null).
#   Quando rp.dependent_id != None, user_id é o guardian e user_phone é o
#   phone do guardian — que é o contato correto pro driver (dependente não
#   possui phone próprio). Por isso não há dependent_phone nem guardian_phone
#   no DTO (redundantes). (US13)
# ===========================================================================


from datetime import datetime
from uuid import UUID, uuid4


def make_response_payload(**kwargs) -> dict:
    defaults = {
        "id": uuid4(),
        "route_id": uuid4(),
        "status": "pending",
        "requested_at": datetime(2026, 4, 18, 10, 0, 0),
        "joined_at": None,
        "user_id": uuid4(),
        "user_name": "João Silva",
        "user_phone": "51999999999",
        "pickup_address_id": uuid4(),
        "dependent_id": None,
        "dependent_name": None,
        "guardian_name": None,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Campos obrigatórios — ausência deve levantar ValidationError
# ---------------------------------------------------------------------------


def test_route_passanger_response_requires_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_route_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["route_id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_status() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["status"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_requested_at() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["requested_at"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_user_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["user_id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_user_name() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["user_name"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_pickup_address_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["pickup_address_id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_requires_user_phone() -> None:
    """US13 — driver precisa do phone do passageiro pro deeplink de contato."""
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["user_phone"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_exposes_user_phone() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(user_phone="54988887777")
    response = RoutePassangerResponse(**payload)
    assert response.user_phone == "54988887777"


# ---------------------------------------------------------------------------
# Campos opcionais — default None quando não fornecidos
# ---------------------------------------------------------------------------


def test_route_passanger_response_joined_at_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["joined_at"]
    response = RoutePassangerResponse(**payload)
    assert response.joined_at is None


def test_route_passanger_response_dependent_id_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["dependent_id"]
    response = RoutePassangerResponse(**payload)
    assert response.dependent_id is None


def test_route_passanger_response_dependent_name_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["dependent_name"]
    response = RoutePassangerResponse(**payload)
    assert response.dependent_name is None


def test_route_passanger_response_guardian_name_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["guardian_name"]
    response = RoutePassangerResponse(**payload)
    assert response.guardian_name is None


def test_route_passanger_response_accepts_explicit_none_on_optionals() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(
        joined_at=None,
        dependent_id=None,
        dependent_name=None,
        guardian_name=None,
    )
    response = RoutePassangerResponse(**payload)
    assert response.joined_at is None
    assert response.dependent_id is None
    assert response.dependent_name is None
    assert response.guardian_name is None


# ---------------------------------------------------------------------------
# Validação de tipos
# ---------------------------------------------------------------------------


def test_route_passanger_response_rejects_invalid_uuid() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(id="not-a-uuid")
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_rejects_invalid_requested_at() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(requested_at="not-a-datetime")
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


def test_route_passanger_response_accepts_uuid_from_string() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    id_str = "12345678-1234-1234-1234-123456789012"
    payload = make_response_payload(id=id_str)
    response = RoutePassangerResponse(**payload)
    assert response.id == UUID(id_str)


def test_route_passanger_response_accepts_datetime_from_iso_string() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    iso = "2026-04-18T10:00:00"
    payload = make_response_payload(requested_at=iso)
    response = RoutePassangerResponse(**payload)
    assert response.requested_at == datetime(2026, 4, 18, 10, 0, 0)


# ---------------------------------------------------------------------------
# Payloads válidos
# ---------------------------------------------------------------------------


def test_route_passanger_response_accepts_valid_payload_without_dependent() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    response = RoutePassangerResponse(**payload)
    assert response.user_name == "João Silva"
    assert response.status == "pending"
    assert response.dependent_id is None
    assert response.dependent_name is None
    assert response.guardian_name is None


def test_route_passanger_response_accepts_valid_payload_with_dependent() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    dependent_id = uuid4()
    payload = make_response_payload(
        dependent_id=dependent_id,
        dependent_name="Maria Silva",
        guardian_name="João Silva",
    )
    response = RoutePassangerResponse(**payload)
    assert response.dependent_id == dependent_id
    assert response.dependent_name == "Maria Silva"
    assert response.guardian_name == "João Silva"


def test_route_passanger_response_accepts_joined_at_datetime() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    joined = datetime(2026, 4, 18, 11, 0, 0)
    payload = make_response_payload(status="accepted", joined_at=joined)
    response = RoutePassangerResponse(**payload)
    assert response.joined_at == joined


def test_route_passanger_response_status_preserves_string_value() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    for status_value in ("pending", "accepted", "rejected", "removed"):
        payload = make_response_payload(status=status_value)
        response = RoutePassangerResponse(**payload)
        assert response.status == status_value


# ---------------------------------------------------------------------------
# ORM mode — from_attributes=True
# ---------------------------------------------------------------------------


def test_route_passanger_response_builds_from_orm_like_object() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    class FakeORMObject:
        pass

    obj = FakeORMObject()
    obj.id = uuid4()
    obj.route_id = uuid4()
    obj.status = "accepted"
    obj.requested_at = datetime(2026, 4, 18, 10, 0, 0)
    obj.joined_at = datetime(2026, 4, 18, 11, 0, 0)
    obj.user_id = uuid4()
    obj.user_name = "João Silva"
    obj.user_phone = "51999999999"
    obj.pickup_address_id = uuid4()
    obj.dependent_id = None
    obj.dependent_name = None
    obj.guardian_name = None

    response = RoutePassangerResponse.model_validate(obj)
    assert response.id == obj.id
    assert response.status == "accepted"
    assert response.user_name == "João Silva"
    assert response.user_phone == "51999999999"
    assert response.pickup_address_id == obj.pickup_address_id


# ===========================================================================
# Erros do domínio — contrato mínimo
# ===========================================================================


def test_route_passanger_not_found_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    assert issubclass(RoutePassangerNotFoundError, Exception)


def test_route_passanger_not_found_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    err = RoutePassangerNotFoundError()
    assert str(err) != ""


def test_route_passanger_not_found_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    err = RoutePassangerNotFoundError("mensagem customizada")
    assert str(err) == "mensagem customizada"


def test_route_capacity_exceeded_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    assert issubclass(RouteCapacityExceededError, Exception)


def test_route_capacity_exceeded_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    err = RouteCapacityExceededError()
    assert str(err) != ""


def test_route_capacity_exceeded_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    err = RouteCapacityExceededError("capacidade cheia")
    assert str(err) == "capacidade cheia"


def test_route_passanger_already_processed_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    assert issubclass(RoutePassangerAlreadyProcessedError, Exception)


def test_route_passanger_already_processed_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    err = RoutePassangerAlreadyProcessedError()
    assert str(err) != ""


def test_route_passanger_already_processed_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    err = RoutePassangerAlreadyProcessedError("já processada")
    assert str(err) == "já processada"


# ===========================================================================
# US08 - TK13: PassangerRouteResponse — item da home do passageiro
# Arquivo: src/domains/route_passangers/dtos.py
# Critérios:
#   Campos obrigatórios: route_id, route_name, driver_name, driver_phone,
#     origin_label, destination_label, expected_time, recurrence (list[str]),
#     status, membership_status, schedules (list), joined_at
#   Opcional: dependent_name (default None)
#   model_config deve permitir construção via from_attributes=True.
#
#   Observação: driver_phone corresponde a user.phone do motorista, resolvido
#   pelo service. Usado pelo FE pra montar deeplink tel:/wa.me (US13).
# ===========================================================================


from datetime import time as dtime


def make_passanger_route_payload(**kwargs) -> dict:
    defaults = {
        "route_id": uuid4(),
        "route_name": "PUCRS",
        "driver_name": "Carlos Motorista",
        "driver_phone": "51999999999",
        "origin_label": "Casa",
        "destination_label": "PUCRS",
        "expected_time": dtime(8, 0),
        "recurrence": ["seg", "ter", "qua", "qui", "sex"],
        "status": "ativa",
        "membership_status": "accepted",
        "schedules": [],
        "joined_at": datetime(2026, 4, 18, 10, 0, 0),
        "dependent_name": None,
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_requires_route_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    del payload["route_id"]
    with pytest.raises(ValidationError):
        PassangerRouteResponse(**payload)


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_requires_membership_status() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    del payload["membership_status"]
    with pytest.raises(ValidationError):
        PassangerRouteResponse(**payload)


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_requires_joined_at() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    del payload["joined_at"]
    with pytest.raises(ValidationError):
        PassangerRouteResponse(**payload)


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_requires_driver_phone() -> None:
    """US13 — passageiro precisa do phone do motorista pro deeplink."""
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    del payload["driver_phone"]
    with pytest.raises(ValidationError):
        PassangerRouteResponse(**payload)


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_exposes_driver_phone() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload(driver_phone="54988887777")
    response = PassangerRouteResponse(**payload)
    assert response.driver_phone == "54988887777"


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_dependent_name_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    del payload["dependent_name"]
    response = PassangerRouteResponse(**payload)
    assert response.dependent_name is None


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_accepts_valid_self_payload() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload()
    response = PassangerRouteResponse(**payload)
    assert response.route_name == "PUCRS"
    assert response.driver_name == "Carlos Motorista"
    assert response.membership_status == "accepted"
    assert response.dependent_name is None


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_accepts_dependent_payload() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    payload = make_passanger_route_payload(dependent_name="Maria Silva")
    response = PassangerRouteResponse(**payload)
    assert response.dependent_name == "Maria Silva"


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_membership_status_preserves_values() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    for status_value in ("pending", "accepted"):
        payload = make_passanger_route_payload(membership_status=status_value)
        response = PassangerRouteResponse(**payload)
        assert response.membership_status == status_value


@pytest.mark.skip(reason="US08-TK13")
def test_passanger_route_response_builds_from_orm_like_object() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteResponse

    class FakeObj:
        pass

    obj = FakeObj()
    obj.route_id = uuid4()
    obj.route_name = "PUCRS"
    obj.driver_name = "Carlos Motorista"
    obj.driver_phone = "51999999999"
    obj.origin_label = "Casa"
    obj.destination_label = "PUCRS"
    obj.expected_time = dtime(8, 0)
    obj.recurrence = ["seg", "qua", "sex"]
    obj.status = "ativa"
    obj.membership_status = "pending"
    obj.schedules = []
    obj.joined_at = datetime(2026, 4, 18, 10, 0, 0)
    obj.dependent_name = None

    response = PassangerRouteResponse.model_validate(obj)
    assert response.route_id == obj.route_id
    assert response.membership_status == "pending"
    assert response.driver_phone == "51999999999"


# ===========================================================================
# US14 - TK01: PassangerRouteDetailResponse + NotRoutePassangerError
# Arquivos:    src/domains/route_passangers/dtos.py
#              src/domains/route_passangers/errors.py
#
# Critérios:
#   DTO PassangerRouteDetailResponse expõe:
#     obrigatórios:
#       route_id, name, route_type, status, recurrence, expected_time,
#       origin_address, destination_address, stops, driver_name, driver_phone,
#       membership_status, my_pickup_address, my_schedules
#     opcionais (default None):
#       dependent_id, dependent_name, current_trip_id
#     model_config deve permitir construção a partir de objetos ORM
#     (from_attributes=True).
#   NÃO pode expor: invite_code, max_passengers, driver_id.
#   Erro: NotRoutePassangerError herda de Exception e possui mensagem default
#     em pt-BR.
# ===========================================================================


def make_detail_payload(**kwargs) -> dict:
    from src.domains.route_passangers.dtos import RoutePassangerScheduleResponse
    from src.domains.routes.dtos import AddressResponse
    from src.domains.stops.dtos import StopResponse

    origin = AddressResponse(
        id=uuid4(),
        label="Casa",
        street="Rua X",
        number="100",
        neighborhood="Centro",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    destination = AddressResponse(
        id=uuid4(),
        label="PUCRS",
        street="Av. Ipiranga",
        number="6681",
        neighborhood="Partenon",
        zip="90619-900",
        city="Porto Alegre",
        state="RS",
    )
    pickup = AddressResponse(
        id=uuid4(),
        label="Embarque",
        street="Rua Z",
        number="200",
        neighborhood="Centro",
        zip="90000-001",
        city="Porto Alegre",
        state="RS",
    )
    defaults = {
        "route_id": uuid4(),
        "name": "PUCRS",
        "route_type": "outbound",
        "status": "ativa",
        "recurrence": ["seg", "qua", "sex"],
        "expected_time": dtime(7, 30),
        "origin_address": origin,
        "destination_address": destination,
        "stops": [],
        "driver_name": "Carlos Motorista",
        "driver_phone": "51999999999",
        "membership_status": "accepted",
        "dependent_id": None,
        "dependent_name": None,
        "my_pickup_address": pickup,
        "my_schedules": [],
        "current_trip_id": None,
    }
    defaults.update(kwargs)
    return defaults


def test_passanger_route_detail_response_accepts_valid_payload() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    response = PassangerRouteDetailResponse(**make_detail_payload())

    assert response.name == "PUCRS"
    assert response.status == "ativa"
    assert response.route_type == "outbound"
    assert response.driver_phone == "51999999999"
    assert response.membership_status == "accepted"


def test_passanger_route_detail_response_requires_route_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    payload = make_detail_payload()
    payload.pop("route_id")
    with pytest.raises(ValidationError):
        PassangerRouteDetailResponse(**payload)


def test_passanger_route_detail_response_requires_driver_phone() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    payload = make_detail_payload()
    payload.pop("driver_phone")
    with pytest.raises(ValidationError):
        PassangerRouteDetailResponse(**payload)


def test_passanger_route_detail_response_requires_my_pickup_address() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    payload = make_detail_payload()
    payload.pop("my_pickup_address")
    with pytest.raises(ValidationError):
        PassangerRouteDetailResponse(**payload)


def test_passanger_route_detail_response_dependent_fields_default_none() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    payload = make_detail_payload()
    payload.pop("dependent_id")
    payload.pop("dependent_name")
    payload.pop("current_trip_id")

    response = PassangerRouteDetailResponse(**payload)
    assert response.dependent_id is None
    assert response.dependent_name is None
    assert response.current_trip_id is None


def test_passanger_route_detail_response_accepts_dependent_fields_when_guardian() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    dep_id = uuid4()
    response = PassangerRouteDetailResponse(
        **make_detail_payload(dependent_id=dep_id, dependent_name="Valentina Fonseca")
    )
    assert response.dependent_id == dep_id
    assert response.dependent_name == "Valentina Fonseca"


def test_passanger_route_detail_response_accepts_current_trip_id_when_in_progress() -> None:
    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    trip_id = uuid4()
    response = PassangerRouteDetailResponse(
        **make_detail_payload(status="em_andamento", current_trip_id=trip_id)
    )
    assert response.status == "em_andamento"
    assert response.current_trip_id == trip_id


def test_passanger_route_detail_response_does_not_expose_driver_id_or_invite_code() -> None:
    """Projeção passageiro-facing — proíbe vazar campos sensíveis do motorista."""
    from src.domains.route_passangers.dtos import PassangerRouteDetailResponse

    fields = set(PassangerRouteDetailResponse.model_fields.keys())
    assert "invite_code" not in fields
    assert "max_passengers" not in fields
    assert "driver_id" not in fields


def test_not_route_passanger_error_has_default_message_in_portuguese() -> None:
    from src.domains.route_passangers.errors import NotRoutePassangerError

    err = NotRoutePassangerError()
    assert isinstance(err, Exception)
    msg = str(err).lower()
    assert any(token in msg for token in ("vínculo", "vinculo", "passageiro", "rota"))
