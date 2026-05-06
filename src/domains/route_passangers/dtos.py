from datetime import datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domains.addresses.dtos import AddressResponse
from src.domains.routes.dtos import AddressCreate
from src.domains.stops.dtos import StopResponse


class RoutePassangerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    status: str
    requested_at: datetime
    user_id: UUID
    user_name: str
    user_phone: str
    pickup_address_id: UUID

    photo_url: str | None = None
    joined_at: datetime | None = None
    dependent_id: UUID | None = None
    dependent_name: str | None = None
    guardian_name: str | None = None


class RoutePassangerScheduleRequest(BaseModel):
    """Item de agendamento enviado pelo passageiro: dia + endereço de embarque.

    Usado pelo UpdateSchedulesRequest (PATCH schedules).
    """

    day_of_week: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] = Field(
        ..., description="Dia da semana em inglês"
    )
    address_id: UUID = Field(..., description="Endereço de embarque neste dia")


class JoinRouteScheduleRequest(BaseModel):
    """Item de agendamento no payload de entrada na rota.

    O endereço de embarque é informado uma única vez em JoinRouteRequest.address
    e é reutilizado em todos os dias — por isso este DTO não carrega address_id.
    """

    day_of_week: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] = Field(
        ..., description="Dia da semana em inglês"
    )


class RoutePassangerScheduleResponse(BaseModel):
    """Representação de um agendamento persistido."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: str
    address_id: UUID


class JoinRouteRequest(BaseModel):
    """Payload para um passageiro solicitar entrada em uma rota.

    O campo `address` define o endereço de embarque que será criado inline pelo
    backend — o frontend não precisa fazer um POST /addresses separado.
    O mesmo endereço é usado como pickup_address em todos os dias da recorrência.
    """

    dependent_id: UUID | None = Field(default=None, description="UUID do dependente, se guardian solicita em seu nome")
    address: AddressCreate = Field(..., description="Endereço de embarque do passageiro (criado inline)")
    schedules: list[JoinRouteScheduleRequest] = Field(..., min_length=1, description="Pelo menos um dia de agendamento")

    @model_validator(mode="after")
    def no_duplicate_days(self) -> "JoinRouteRequest":
        """Verifica se não há dias duplicados na lista de agendamentos."""
        days = [s.day_of_week for s in self.schedules]
        if len(days) != len(set(days)):
            raise ValueError("Agendamentos não podem ter dias da semana duplicados.")
        return self


class UpdateSchedulesRequest(BaseModel):
    """Payload para o passageiro atualizar seus dias de participação."""

    schedules: list[RoutePassangerScheduleRequest] = Field(..., min_length=1, description="Pelo menos um dia de agendamento")

    @model_validator(mode="after")
    def no_duplicate_days(self) -> "UpdateSchedulesRequest":
        """Verifica se não há dias duplicados na lista de agendamentos."""
        days = [s.day_of_week for s in self.schedules]
        if len(days) != len(set(days)):
            raise ValueError("Agendamentos não podem ter dias da semana duplicados.")
        return self


class PassangerRouteResponse(BaseModel):
    """Item da lista 'Minhas Rotas' da home do passageiro."""

    model_config = ConfigDict(from_attributes=True)

    route_id: UUID
    route_name: str
    driver_name: str
    driver_phone: str
    origin_label: str
    destination_label: str
    expected_time: time
    recurrence: list[str]
    status: str
    membership_status: str
    schedules: list[RoutePassangerScheduleResponse]
    joined_at: datetime
    dependent_name: str | None = None


# ---------------------------------------------------------------------------
# Detalhes da rota para o passageiro (tela 2.3)
# ---------------------------------------------------------------------------


class PassangerRouteDetailResponse(BaseModel):
    """Detalhe completo da rota do ponto de vista do passageiro (tela 2.3).

    Projeção passageiro-facing — NÃO expõe invite_code, max_passengers nem
    driver_id. Retornada por GET /routes/{route_id}/me.
    """

    model_config = ConfigDict(from_attributes=True)

    route_id: UUID
    name: str
    route_type: str
    status: str
    recurrence: list[str]
    expected_time: time

    origin_address: AddressResponse
    destination_address: AddressResponse
    stops: list[StopResponse]

    driver_name: str
    driver_phone: str

    membership_status: str
    dependent_id: UUID | None = None
    dependent_name: str | None = None
    my_pickup_address: AddressResponse
    my_schedules: list[RoutePassangerScheduleResponse]

    current_trip_id: UUID | None = None
