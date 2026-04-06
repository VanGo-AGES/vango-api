from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.infrastructure.dependencies.route_dependencies import get_route_service

from .dtos import RouteCreate, RouteResponse
from .errors import NoVehicleError, RouteNotFoundError, RouteOwnershipError
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
) -> list[RouteResponse]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")


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
) -> RouteResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")
