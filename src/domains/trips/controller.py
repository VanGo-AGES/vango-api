"""US09 — Endpoints de execução de viagem."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.domains.routes.errors import (
    RouteNotFoundError,
    RouteOwnershipError,
)
from src.domains.trips.dtos import (
    FinishTripRequest,
    StartTripRequest,
    TripNextStopResponse,
    TripPassangerResponse,
    TripResponse,
)
from src.domains.trips.errors import (
    InvalidTripPassangerStatusError,
    NoPassangersToStartError,
    TripAlreadyFinishedError,
    TripAlreadyInProgressError,
    TripNotFoundError,
    TripNotInProgressError,
    TripOwnershipError,
    TripPassangerNotFoundError,
    TripStopNotFoundError,
    VehicleNotOwnedError,
)
from src.domains.trips.service import TripService
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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripResponse:
    try:
        return service.start_trip(route_id, UUID(x_user_id), data)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RouteOwnershipError, TripOwnershipError) as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except VehicleNotOwnedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except TripAlreadyInProgressError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NoPassangersToStartError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


# US09-TK15
@router.get(
    "/trips/{trip_id}",
    response_model=TripResponse,
    summary="Detalhes da viagem em andamento (motorista)",
)
def get_trip(
    trip_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripResponse:
    try:
        driver_id = UUID(x_user_id)
        return service.get_current_trip(trip_id, driver_id)
    except TripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


# US09-TK16
@router.get(
    "/trips/{trip_id}/next-stop",
    response_model=TripNextStopResponse | None,
    summary="Próxima parada pendente + info do passageiro",
)
def get_next_stop(
    trip_id: UUID,
    service: Annotated[TripService, Depends(get_trip_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripNextStopResponse | None:
    try:
        return service.get_next_stop(trip_id, UUID(x_user_id))
    except TripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripPassangerResponse:
    try:
        return service.board_passanger(trip_id, trip_passanger_id, UUID(x_user_id))
    except (TripNotFoundError, TripPassangerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (TripNotInProgressError, InvalidTripPassangerStatusError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripPassangerResponse:
    try:
        return service.mark_passanger_absent(trip_id, trip_passanger_id, UUID(x_user_id))
    except (TripNotFoundError, TripPassangerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (TripNotInProgressError, InvalidTripPassangerStatusError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> list[TripPassangerResponse]:
    try:
        return service.skip_stop(trip_id, stop_id, UUID(x_user_id))
    except TripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripStopNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TripNotInProgressError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripPassangerResponse:
    try:
        return service.alight_passanger(trip_id, trip_passanger_id, UUID(x_user_id))
    except (TripNotFoundError, TripPassangerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (TripNotInProgressError, InvalidTripPassangerStatusError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> TripResponse:
    try:
        return service.finish_trip(trip_id, UUID(x_user_id), data)
    except TripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TripOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TripAlreadyFinishedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
