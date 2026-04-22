"""US08-TK01 — DTOs de schedules / join / update do domínio route_passangers.

Arquivos:
  src/domains/route_passangers/dtos.py

DTOs cobertos:
  - RoutePassangerScheduleRequest: day_of_week (str), address_id (UUID)
  - RoutePassangerScheduleResponse: id (UUID), day_of_week (str), address_id (UUID)
      model_config = from_attributes=True
  - JoinRouteRequest: dependent_id (UUID | None, default=None),
      schedules (list[RoutePassangerScheduleRequest], min_length=1)
  - UpdateSchedulesRequest: schedules (list[RoutePassangerScheduleRequest], min_length=1)

Validações esperadas:
  - day_of_week aceita apenas: 'monday', 'tuesday', 'wednesday', 'thursday',
    'friday', 'saturday', 'sunday'
  - schedules não pode ter day_of_week duplicado no mesmo payload
  - schedules deve ter pelo menos 1 item
"""

from uuid import UUID, uuid4

import pytest


VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def make_schedule_item(**kwargs) -> dict:
    defaults = {"day_of_week": "monday", "address_id": uuid4()}
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# RoutePassangerScheduleRequest
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_request_requires_day_of_week() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerScheduleRequest

    with pytest.raises(ValidationError):
        RoutePassangerScheduleRequest(address_id=uuid4())


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_request_requires_address_id() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerScheduleRequest

    with pytest.raises(ValidationError):
        RoutePassangerScheduleRequest(day_of_week="monday")


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_request_accepts_valid_days() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerScheduleRequest

    for day in VALID_DAYS:
        req = RoutePassangerScheduleRequest(day_of_week=day, address_id=uuid4())
        assert req.day_of_week == day


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_request_rejects_invalid_day() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerScheduleRequest

    with pytest.raises(ValidationError):
        RoutePassangerScheduleRequest(day_of_week="segunda", address_id=uuid4())


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_request_rejects_invalid_address_uuid() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerScheduleRequest

    with pytest.raises(ValidationError):
        RoutePassangerScheduleRequest(day_of_week="monday", address_id="not-a-uuid")


# ---------------------------------------------------------------------------
# RoutePassangerScheduleResponse
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_response_builds_from_orm_like_object() -> None:
    from src.domains.route_passangers.dtos import RoutePassangerScheduleResponse

    class FakeORM:
        pass

    obj = FakeORM()
    obj.id = uuid4()
    obj.day_of_week = "monday"
    obj.address_id = uuid4()

    response = RoutePassangerScheduleResponse.model_validate(obj)
    assert response.id == obj.id
    assert response.day_of_week == "monday"
    assert response.address_id == obj.address_id


@pytest.mark.skip(reason="US08-TK01")
def test_schedule_response_requires_all_fields() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import RoutePassangerScheduleResponse

    with pytest.raises(ValidationError):
        RoutePassangerScheduleResponse()


# ---------------------------------------------------------------------------
# JoinRouteRequest
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_requires_schedules() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import JoinRouteRequest

    with pytest.raises(ValidationError):
        JoinRouteRequest()


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_rejects_empty_schedules() -> None:
    """schedules precisa ter ao menos 1 item."""
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import JoinRouteRequest

    with pytest.raises(ValidationError):
        JoinRouteRequest(schedules=[])


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_dependent_id_defaults_to_none() -> None:
    from src.domains.route_passangers.dtos import JoinRouteRequest

    req = JoinRouteRequest(schedules=[make_schedule_item()])
    assert req.dependent_id is None


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_accepts_dependent_id() -> None:
    from src.domains.route_passangers.dtos import JoinRouteRequest

    dep_id = uuid4()
    req = JoinRouteRequest(dependent_id=dep_id, schedules=[make_schedule_item()])
    assert req.dependent_id == dep_id


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_accepts_multiple_schedules() -> None:
    from src.domains.route_passangers.dtos import JoinRouteRequest

    req = JoinRouteRequest(
        schedules=[
            make_schedule_item(day_of_week="monday"),
            make_schedule_item(day_of_week="wednesday"),
            make_schedule_item(day_of_week="friday"),
        ]
    )
    assert len(req.schedules) == 3


@pytest.mark.skip(reason="US08-TK01")
def test_join_route_request_rejects_duplicate_day() -> None:
    """Não pode ter o mesmo day_of_week repetido."""
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import JoinRouteRequest

    with pytest.raises(ValidationError):
        JoinRouteRequest(
            schedules=[
                make_schedule_item(day_of_week="monday"),
                make_schedule_item(day_of_week="monday"),
            ]
        )


# ---------------------------------------------------------------------------
# UpdateSchedulesRequest
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US08-TK01")
def test_update_schedules_request_requires_schedules() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import UpdateSchedulesRequest

    with pytest.raises(ValidationError):
        UpdateSchedulesRequest()


@pytest.mark.skip(reason="US08-TK01")
def test_update_schedules_request_rejects_empty_schedules() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import UpdateSchedulesRequest

    with pytest.raises(ValidationError):
        UpdateSchedulesRequest(schedules=[])


@pytest.mark.skip(reason="US08-TK01")
def test_update_schedules_request_accepts_valid_payload() -> None:
    from src.domains.route_passangers.dtos import UpdateSchedulesRequest

    req = UpdateSchedulesRequest(
        schedules=[
            make_schedule_item(day_of_week="monday"),
            make_schedule_item(day_of_week="tuesday"),
        ]
    )
    assert len(req.schedules) == 2


@pytest.mark.skip(reason="US08-TK01")
def test_update_schedules_request_rejects_duplicate_day() -> None:
    from pydantic import ValidationError

    from src.domains.route_passangers.dtos import UpdateSchedulesRequest

    with pytest.raises(ValidationError):
        UpdateSchedulesRequest(
            schedules=[
                make_schedule_item(day_of_week="tuesday"),
                make_schedule_item(day_of_week="tuesday"),
            ]
        )


# ---------------------------------------------------------------------------
# DuplicateRoutePassangerError (já vai direto no código, smoke test apenas)
# ---------------------------------------------------------------------------


def test_duplicate_route_passanger_error_inherits_from_exception() -> None:
    from src.domains.route_passangers.errors import DuplicateRoutePassangerError

    assert issubclass(DuplicateRoutePassangerError, Exception)


def test_duplicate_route_passanger_error_accepts_custom_message() -> None:
    from src.domains.route_passangers.errors import DuplicateRoutePassangerError

    err = DuplicateRoutePassangerError("vínculo ativo existente")
    assert str(err) == "vínculo ativo existente"
