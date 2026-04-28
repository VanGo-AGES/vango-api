"""
US06 — Controller de route_passangers.

Endpoints:
- POST   /routes/{route_id}/passangers/{rp_id}/accept   (TK09)
- POST   /routes/{route_id}/passangers/{rp_id}/reject   (TK11)
- DELETE /routes/{route_id}/passangers/{rp_id}          (TK13)
- GET    /routes/{route_id}/passangers?status=pending   (TK15)
- GET    /routes/me                                     (US08-TK15)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from src.domains.routes.errors import RouteNotFoundError, RouteOwnershipError
from src.infrastructure.dependencies.route_passanger_dependencies import (
    get_route_passanger_service,
)

from .dtos import (
    JoinRouteRequest,
    PassangerRouteDetailResponse,
    PassangerRouteResponse,
    RoutePassangerResponse,
    UpdateSchedulesRequest,
)
from .errors import NotRoutePassangerError
from .service import RoutePassangerService

router = APIRouter(prefix="/routes", tags=["RoutePassangers"])


# US08-TK15
# IMPORTANTE: este endpoint precisa ser resolvido ANTES de
# GET /routes/{route_id} (que vive em routes.controller). Por isso
# route_passanger_controller é registrado antes de route_controller em main.py.
@router.get(
    "/me",
    response_model=list[PassangerRouteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar minhas rotas (home do passageiro)",
    description=(
        "Retorna todos os vínculos ativos (pending + accepted) do usuário "
        "autenticado, incluindo vínculos em que ele é guardian de um dependente. "
        "Ordenado por joined_at desc. Usado pela home do passageiro."
    ),
)
def list_my_routes(
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> list[PassangerRouteResponse]:
    return service.list_my_routes(UUID(x_user_id))


# US06-TK09
@router.post(
    "/{route_id}/passangers/{rp_id}/accept",
    response_model=RoutePassangerResponse,
    status_code=status.HTTP_200_OK,
    summary="Aceitar solicitação de passageiro",
    description=("Aprova uma solicitação pending. Valida ownership, bloqueio de rota em andamento e capacidade máxima do veículo."),
)
def accept_request(
    route_id: UUID,
    rp_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RoutePassangerResponse:
    pass


# US06-TK11
@router.post(
    "/{route_id}/passangers/{rp_id}/reject",
    response_model=RoutePassangerResponse,
    status_code=status.HTTP_200_OK,
    summary="Recusar solicitação de passageiro",
    description=("Recusa uma solicitação pending. Valida ownership e bloqueio de rota em andamento. Não valida capacidade."),
)
def reject_request(
    route_id: UUID,
    rp_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RoutePassangerResponse:
    pass


# US06-TK13
@router.delete(
    "/{route_id}/passangers/{rp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover passageiro da rota",
    description="Remove um passageiro da rota. Bloqueado se a rota estiver em andamento.",
)
def remove_passanger(
    route_id: UUID,
    rp_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> None:
    pass


# US06-TK15
@router.get(
    "/{route_id}/passangers",
    response_model=list[RoutePassangerResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar passageiros/solicitações da rota",
    description=(
        "Lista vínculos de passageiros da rota. Aceita filtro opcional por status (pending, accepted, rejected). Sem filtro retorna todos."
    ),
)
def list_passangers(
    route_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[RoutePassangerResponse]:
    try:
        driver_id = UUID(x_user_id)
        return service.list_by_status(route_id, driver_id, status=status_filter)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RouteOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# US08-TK08
@router.post(
    "/{route_id}/passangers",
    response_model=RoutePassangerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar entrada em rota",
    description=(
        "Passageiro (ou guardian em nome de dependente) solicita entrada na rota "
        "informando schedules (dias + endereço de embarque). Cria vínculo pending."
    ),
)
def join_route(
    route_id: UUID,
    body: JoinRouteRequest,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
) -> RoutePassangerResponse:
    pass


# US08-TK10
@router.delete(
    "/{route_id}/passangers/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sair de uma rota",
    description=(
        "Passageiro sai da rota. Aceita dependent_id opcional quando guardian "
        "está saindo em nome do dependente. Bloqueado se rota está em andamento."
    ),
)
def leave_route(
    route_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    dependent_id: Annotated[UUID | None, Query()] = None,
) -> None:
    pass


# US08-TK12
@router.patch(
    "/{route_id}/passangers/me",
    response_model=RoutePassangerResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar schedules de participação",
    description=(
        "Substitui completamente os schedules atuais do passageiro pelos "
        "fornecidos. Aceita dependent_id opcional para guardian em nome de dep."
    ),
)
def update_schedules(
    route_id: UUID,
    body: UpdateSchedulesRequest,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    dependent_id: Annotated[UUID | None, Query()] = None,
) -> RoutePassangerResponse:
    pass


# IMPORTANTE: este endpoint precisa ser resolvido ANTES de
# GET /routes/{route_id} (que vive em routes.controller). Por isso
# route_passanger_controller é registrado antes de route_controller em main.py.
@router.get(
    "/{route_id}/me",
    response_model=PassangerRouteDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Detalhe da rota para o passageiro",
    description=(
        "Retorna o detalhe completo da rota do ponto de vista do passageiro "
        "autenticado. Aceita dependent_id opcional quando guardian "
        "está vendo em nome do dependente. Não expõe invite_code/max_passengers/"
        "driver_id. Erros: 404 se a rota não existir, 403 se o usuário não tiver "
        "vínculo ativo com a rota."
    ),
)
def get_my_route_detail(
    route_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    dependent_id: Annotated[UUID | None, Query()] = None,
) -> PassangerRouteDetailResponse:
    try:
        return service.get_my_route_detail(route_id, UUID(x_user_id), dependent_id)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except NotRoutePassangerError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
