import pytest

# ===========================================================================
# US06 - TK05: RoutePassangerResponse + Erros do domínio route_passangers
# Arquivos:    src/domains/route_passangers/dtos.py
#              src/domains/route_passangers/errors.py
# Critérios:
#   DTO RoutePassangerResponse expõe:
#     obrigatórios: id, route_id, status, requested_at, user_id, user_name
#     opcionais (default None): joined_at, dependent_id, dependent_name,
#                                guardian_name
#     model_config deve permitir construção a partir de objetos ORM
#     (from_attributes=True).
#   Erros: RoutePassangerNotFoundError, RouteCapacityExceededError,
#          RoutePassangerAlreadyProcessedError — todos herdam de Exception
#          e possuem mensagem default em pt-BR.
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
        "dependent_id": None,
        "dependent_name": None,
        "guardian_name": None,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Campos obrigatórios — ausência deve levantar ValidationError
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_route_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["route_id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_status() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["status"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_requested_at() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["requested_at"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_user_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["user_id"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_requires_user_name() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["user_name"]
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


# ---------------------------------------------------------------------------
# Campos opcionais — default None quando não fornecidos
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_joined_at_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["joined_at"]
    response = RoutePassangerResponse(**payload)
    assert response.joined_at is None


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_dependent_id_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["dependent_id"]
    response = RoutePassangerResponse(**payload)
    assert response.dependent_id is None


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_dependent_name_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["dependent_name"]
    response = RoutePassangerResponse(**payload)
    assert response.dependent_name is None


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_guardian_name_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    del payload["guardian_name"]
    response = RoutePassangerResponse(**payload)
    assert response.guardian_name is None


@pytest.mark.skip(reason="US06-TK05")
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


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_rejects_invalid_uuid() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(id="not-a-uuid")
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_rejects_invalid_requested_at() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload(requested_at="not-a-datetime")
    with pytest.raises(ValidationError):
        RoutePassangerResponse(**payload)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_accepts_uuid_from_string() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    id_str = "12345678-1234-1234-1234-123456789012"
    payload = make_response_payload(id=id_str)
    response = RoutePassangerResponse(**payload)
    assert response.id == UUID(id_str)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_accepts_datetime_from_iso_string() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    iso = "2026-04-18T10:00:00"
    payload = make_response_payload(requested_at=iso)
    response = RoutePassangerResponse(**payload)
    assert response.requested_at == datetime(2026, 4, 18, 10, 0, 0)


# ---------------------------------------------------------------------------
# Payloads válidos
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_accepts_valid_payload_without_dependent() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    payload = make_response_payload()
    response = RoutePassangerResponse(**payload)
    assert response.user_name == "João Silva"
    assert response.status == "pending"
    assert response.dependent_id is None
    assert response.dependent_name is None
    assert response.guardian_name is None


@pytest.mark.skip(reason="US06-TK05")
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


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_accepts_joined_at_datetime() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    joined = datetime(2026, 4, 18, 11, 0, 0)
    payload = make_response_payload(status="accepted", joined_at=joined)
    response = RoutePassangerResponse(**payload)
    assert response.joined_at == joined


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_response_status_preserves_string_value() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerResponse

    for status_value in ("pending", "accepted", "rejected", "removed"):
        payload = make_response_payload(status=status_value)
        response = RoutePassangerResponse(**payload)
        assert response.status == status_value


# ---------------------------------------------------------------------------
# ORM mode — from_attributes=True
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US06-TK05")
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
    obj.dependent_id = None
    obj.dependent_name = None
    obj.guardian_name = None

    response = RoutePassangerResponse.model_validate(obj)
    assert response.id == obj.id
    assert response.status == "accepted"
    assert response.user_name == "João Silva"


# ===========================================================================
# Erros do domínio — contrato mínimo
# ===========================================================================


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_not_found_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    assert issubclass(RoutePassangerNotFoundError, Exception)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_not_found_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    err = RoutePassangerNotFoundError()
    assert str(err) != ""


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_not_found_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerNotFoundError

    err = RoutePassangerNotFoundError("mensagem customizada")
    assert str(err) == "mensagem customizada"


@pytest.mark.skip(reason="US06-TK05")
def test_route_capacity_exceeded_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    assert issubclass(RouteCapacityExceededError, Exception)


@pytest.mark.skip(reason="US06-TK05")
def test_route_capacity_exceeded_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    err = RouteCapacityExceededError()
    assert str(err) != ""


@pytest.mark.skip(reason="US06-TK05")
def test_route_capacity_exceeded_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RouteCapacityExceededError

    err = RouteCapacityExceededError("capacidade cheia")
    assert str(err) == "capacidade cheia"


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_already_processed_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    assert issubclass(RoutePassangerAlreadyProcessedError, Exception)


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_already_processed_error_has_default_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    err = RoutePassangerAlreadyProcessedError()
    assert str(err) != ""


@pytest.mark.skip(reason="US06-TK05")
def test_route_passanger_already_processed_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import RoutePassangerAlreadyProcessedError

    err = RoutePassangerAlreadyProcessedError("já processada")
    assert str(err) == "já processada"
