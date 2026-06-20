"""US09 — Endpoints de execução de viagem."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.domains.trips.dtos import (
    CurrentTripResponse,
    FinishTripRequest,
    StartTripRequest,
    TripNextStopResponse,
    TripPassangerResponse,
    TripResponse,
)
from src.domains.trips.service import TripService
from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import get_current_driver, get_current_user
from src.infrastructure.dependencies.trip_dependencies import get_trip_service

router = APIRouter(tags=["Trips"])


# US09-TK14
@router.post(
    "/routes/{route_id}/trips",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Motorista inicia a execução da rota",
)
def start_trip(
    route_id: UUID,
    data: StartTripRequest,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripResponse:
    return service.start_trip(route_id, current_user.id, data)


# US09-TK15
@router.get(
    "/trips/{trip_id}",
    response_model=TripResponse,
    summary="Detalhes da viagem em andamento (motorista)",
)
def get_trip(
    trip_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripResponse:
    return service.get_current_trip(trip_id, current_user.id)


# US09-TK16
@router.get(
    "/trips/{trip_id}/next-stop",
    response_model=TripNextStopResponse | None,
    summary="Próxima parada pendente + info do passageiro",
)
def get_next_stop(
    trip_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripNextStopResponse | None:
    return service.get_next_stop(trip_id, current_user.id)


# US09-TK17
@router.post(
    "/trips/{trip_id}/passangers/{trip_passanger_id}/board",
    response_model=TripPassangerResponse,
    summary="Motorista confirma embarque de um passageiro",
)
def board_passanger(
    trip_id: UUID,
    trip_passanger_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripPassangerResponse:
    return service.board_passanger(trip_id, trip_passanger_id, current_user.id)


# US09-TK18
@router.post(
    "/trips/{trip_id}/passangers/{trip_passanger_id}/absent",
    response_model=TripPassangerResponse,
    summary="Motorista marca passageiro como não embarcado",
)
def mark_passanger_absent(
    trip_id: UUID,
    trip_passanger_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripPassangerResponse:
    return service.mark_passanger_absent(trip_id, trip_passanger_id, current_user.id)


# US09-TK19
@router.post(
    "/trips/{trip_id}/stops/{stop_id}/skip",
    response_model=list[TripPassangerResponse],
    summary="Motorista pula uma parada (marca passageiros como ausente)",
)
def skip_stop(
    trip_id: UUID,
    stop_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> list[TripPassangerResponse]:
    return service.skip_stop(trip_id, stop_id, current_user.id)


# US09-TK20
@router.post(
    "/trips/{trip_id}/passangers/{trip_passanger_id}/alight",
    response_model=TripPassangerResponse,
    summary="Motorista registra desembarque manual de um passageiro",
)
def alight_passanger(
    trip_id: UUID,
    trip_passanger_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripPassangerResponse:
    return service.alight_passanger(trip_id, trip_passanger_id, current_user.id)


# US09-TK21
@router.post(
    "/trips/{trip_id}/finish",
    response_model=TripResponse,
    summary="Motorista finaliza a viagem",
)
def finish_trip(
    trip_id: UUID,
    data: FinishTripRequest,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> TripResponse:
    return service.finish_trip(trip_id, current_user.id, data)


# US11-TK01 — viagem atual para o passageiro
@router.get(
    "/routes/{route_id}/trips/current",
    response_model=CurrentTripResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Passageiro consulta viagem em andamento da sua rota",
    description=(
        "Retorna o trip_id e status da viagem iniciada na rota, se existir. "
        "Qualquer usuário com vínculo ativo (pending ou accepted) pode consultar — "
        "não é restrito ao motorista. Aceita dependent_id opcional para guardian "
        "consultando em nome do dependente. Retorna null quando não há viagem "
        "em andamento. 404 se a rota não existir. 403 se o usuário não tiver vínculo ativo."
    ),
)
def get_current_trip_for_passanger(
    route_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    dependent_id: Annotated[UUID | None, Query()] = None,
) -> CurrentTripResponse | None:
    return service.get_current_trip_for_passanger(
        route_id,
        current_user.id,
        dependent_id=dependent_id,
    )
