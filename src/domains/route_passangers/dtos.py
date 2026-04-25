from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domains.routes.dtos import AddressResponse
from src.domains.stops.dtos import StopResponse


class RoutePassangerResponse(BaseModel):
    pass


class RoutePassangerScheduleRequest(BaseModel):
    """Item de agendamento enviado pelo passageiro: dia + endereço de embarque."""

    day_of_week: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] = Field(
        ..., description="Dia da semana em inglês"
    )
    address_id: UUID = Field(..., description="Endereço de embarque neste dia")


class RoutePassangerScheduleResponse(BaseModel):
    """Representação de um agendamento persistido."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: str
    address_id: UUID


class JoinRouteRequest(BaseModel):
    """Payload para um passageiro solicitar entrada em uma rota."""

    dependent_id: UUID | None = Field(default=None, description="UUID do dependente, se guardian solicita em seu nome")
    schedules: list[RoutePassangerScheduleRequest] = Field(..., min_length=1, description="Pelo menos um dia de agendamento")

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

    pass


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
