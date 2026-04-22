from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domains.routes.dtos import AddressResponse
from src.domains.stops.dtos import StopResponse


class RoutePassangerResponse(BaseModel):
    pass


class RoutePassangerScheduleRequest(BaseModel):
    """Item de agendamento enviado pelo passageiro: dia + endereço de embarque."""

    pass


class RoutePassangerScheduleResponse(BaseModel):
    """Representação de um agendamento persistido."""

    pass


class JoinRouteRequest(BaseModel):
    """Payload para um passageiro solicitar entrada em uma rota."""

    pass


class UpdateSchedulesRequest(BaseModel):
    """Payload para o passageiro atualizar seus dias de participação."""

    pass


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
