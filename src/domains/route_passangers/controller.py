"""
US06 — Controller de route_passangers.

Endpoints:
- POST   /routes/{route_id}/passangers/{rp_id}/accept   (TK09)
- POST   /routes/{route_id}/passangers/{rp_id}/reject   (TK11)
- DELETE /routes/{route_id}/passangers/{rp_id}          (TK13)
- GET    /routes/{route_id}/passangers?status=pending   (TK15)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from src.infrastructure.dependencies.route_passanger_dependencies import (
    get_route_passanger_service,
)

from .dtos import RoutePassangerResponse
from .service import RoutePassangerService

router = APIRouter(prefix="/routes", tags=["RoutePassangers"])


# US06-TK09
@router.post(
    "/{route_id}/passangers/{rp_id}/accept",
    response_model=RoutePassangerResponse,
    status_code=status.HTTP_200_OK,
    summary="Aceitar solicitação de passageiro",
    description=("Aprova uma solicitação pending. Valida ownership, bloqueio de rota " "em andamento e capacidade máxima do veículo."),
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
    description=("Recusa uma solicitação pending. Valida ownership e bloqueio de rota em andamento. " "Não valida capacidade."),
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
        "Lista vínculos de passageiros da rota. Aceita filtro opcional por status "
        "(pending, accepted, rejected). Sem filtro retorna todos."
    ),
)
def list_passangers(
    route_id: UUID,
    service: Annotated[RoutePassangerService, Depends(get_route_passanger_service)],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[RoutePassangerResponse]:
    pass
