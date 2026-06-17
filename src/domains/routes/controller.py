from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.domains.absences.dtos import RouteAbsenceResponse
from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import get_current_driver, get_current_user
from src.infrastructure.dependencies.route_dependencies import get_route_service

from .dtos import (
    RouteCreate,
    RouteInviteSummaryResponse,
    RouteResponse,
    RouteUpdate,
)
from .errors import (
    NoVehicleError,
    RouteInProgressError,
    RouteNotFoundError,
    RouteOwnershipError,
)
from .service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])


def _safe_route_totals(service: RouteService, route: object) -> tuple[float | None, int | None]:
    totals = service.get_route_totals(route)
    if isinstance(totals, tuple) and len(totals) == 2:
        return totals
    return None, None


def _safe_active_trip_id(service: RouteService, route_id: UUID) -> UUID | None:
    result = service.get_active_trip_id(route_id)
    if result is None or isinstance(result, UUID):
        return result
    return None


_DESCRIPTION_CREATE = (
    "Cria uma rota para o motorista com origem, destino, horário e recorrência. "
    "Gera automaticamente o código de convite e salva com status inativa."
)


@router.post(
    "/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar uma nova rota",
    description=_DESCRIPTION_CREATE,
)
def create_route(
    body: RouteCreate,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> RouteResponse:
    try:
        created_route = service.create_route(current_user.id, body)
        return created_route
    except NoVehicleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{route_id}/invite-code/regenerate",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Revogar e gerar novo código de convite",
    description="Invalida o código de convite atual e gera um novo. Apenas o motorista dono da rota pode realizar esta ação.",
)
def regenerate_invite_code(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> RouteResponse:
    try:
        updated_route = service.regenerate_invite_code(route_id, current_user.id)
        return updated_route
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RouteOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.get(
    "/",
    response_model=list[RouteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas as rotas do motorista",
    description="Retorna todas as rotas cadastradas pelo motorista, independente de status.",
)
def list_routes(
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> list[RouteResponse]:
    driver_id = current_user.id
    routes = service.get_routes(driver_id)
    responses: list[RouteResponse] = []
    for route in routes:
        total_distance_km, estimated_duration_min = _safe_route_totals(service, route)
        active_trip_id = _safe_active_trip_id(service, route.id)
        responses.append(
            RouteResponse.from_orm(route).model_copy(
                update={
                    "total_distance_km": total_distance_km,
                    "estimated_duration_min": estimated_duration_min,
                    "active_trip_id": active_trip_id,
                }
            )
        )
    return responses


# US06-TK04
@router.put(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Editar rota",
    description=(
        "Atualiza uma rota existente do motorista. Permite alteração parcial "
        "(name, route_type, origin, destination, expected_time, recurrence). "
        "Rotas com status='em_andamento' não podem ser editadas."
    ),
)
def update_route(
    route_id: UUID,
    body: RouteUpdate,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> RouteResponse:
    driver_id = current_user.id
    try:
        return service.update_route(route_id, driver_id, body)
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RouteOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RouteInProgressError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# US08-TK06
@router.get(
    "/invite/{invite_code}",
    response_model=RouteInviteSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Resumo de rota por código de convite",
    description=(
        "Retorna o resumo público da rota identificada pelo invite_code, para que "
        "o passageiro decida se solicita entrada. Inclui accepted_count (quantidade "
        "de passageiros já aceitos) mas não expõe invite_code, status nem stops."
    ),
)
def get_route_by_invite_code(
    invite_code: str,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> RouteInviteSummaryResponse:
    try:
        return service.get_invite_summary(invite_code)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get(
    "/{route_id}/absences",
    response_model=list[RouteAbsenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Ausências da rota numa data",
    description=(
        "Retorna os passageiros que avisaram ausência na data informada. "
        "Usado pelo motorista para separar stops presentes de ausentes na "
        "próxima partida. date padrão: hoje (UTC). "
        "403 se não for dono da rota. 404 se a rota não existir."
    ),
)
def list_route_absences(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    date: Annotated[date, Query()] = None,
) -> list[RouteAbsenceResponse]:
    caller_id = current_user.id
    absence_date = datetime.combine(date or datetime.now(UTC).date(), datetime.min.time())
    try:
        return service.get_route_absences(route_id, caller_id, absence_date)
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RouteOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Detalhe de uma rota",
    description="Retorna os dados completos de uma rota, incluindo endereços de origem e destino.",
)
def get_route(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> RouteResponse:
    driver_id = current_user.id
    try:
        route = service.get_route(route_id, driver_id)
        accepted_count = service.get_accepted_count(route_id)
        total_distance_km, estimated_duration_min = _safe_route_totals(service, route)
        active_trip_id = _safe_active_trip_id(service, route_id)
        return RouteResponse.from_orm(route).model_copy(
            update={
                "accepted_count": accepted_count,
                "total_distance_km": total_distance_km,
                "estimated_duration_min": estimated_duration_min,
                "active_trip_id": active_trip_id,
            }
        )
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RouteOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


# US06-TK19
@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir rota",
    description=(
        "Exclui uma rota do motorista. Apenas o motorista dono pode excluir. "
        "Rotas com status='em_andamento' não podem ser excluídas. "
        "Passageiros ativos (pending/accepted) são notificados antes da exclusão. "
        "A remoção é em cascata: route_passangers, schedules e stops associadas "
        "também são apagados."
    ),
)
def delete_route(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
    current_user: Annotated[UserModel, Depends(get_current_driver)],
) -> None:
    driver_id = current_user.id
    try:
        service.delete_route(route_id, driver_id)
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RouteOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RouteInProgressError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
