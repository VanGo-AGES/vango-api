from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.infrastructure.dependencies.route_dependencies import get_route_service

from .dtos import (
    RouteCreate,
    RouteInviteSummaryResponse,
    RouteResponse,
    RouteUpdate,
)
from .errors import (
    NoVehicleError,
    RouteNotFoundError,
    RouteOwnershipError,
)
from .service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])

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
    driver_id: Annotated[UUID, Header(alias="X-User-Id")],
) -> RouteResponse:
    try:
        created_route = service.create_route(driver_id, body)
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
    driver_id: Annotated[UUID, Header(alias="X-User-Id")],
) -> RouteResponse:
    try:
        updated_route = service.regenerate_invite_code(route_id, driver_id)
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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> list[RouteResponse]:
    driver_id = UUID(x_user_id)
    routes = service.get_routes(driver_id)
    return [RouteResponse.from_orm(route) for route in routes]


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RouteResponse:
    pass


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RouteInviteSummaryResponse:
    pass


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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RouteResponse:
    driver_id = UUID(x_user_id)
    try:
        route = service.get_route(route_id, driver_id)
        return RouteResponse.from_orm(route)
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
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> None:
    pass
