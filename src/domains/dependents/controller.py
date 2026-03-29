from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.infrastructure.dependencies.auth_dependencies import get_current_user
from src.infrastructure.dependencies.dependent_dependencies import get_dependent_service

from .dtos import DependentCreate, DependentResponse, DependentUpdate
from .service import DependentService

router = APIRouter(prefix="/dependents", tags=["Dependents"])


@router.post(
    "/",
    response_model=DependentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar dependente",
    description="Permite que um passageiro ou responsável adicione um dependente ao seu perfil.",
)
def create_dependent(
    body: DependentCreate,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DependentResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")


@router.get(
    "/",
    response_model=list[DependentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar dependentes do usuário",
    description="Retorna todos os dependentes cadastrados pelo usuário logado.",
)
def list_dependents(
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[DependentResponse]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")


@router.get(
    "/{dependent_id}",
    response_model=DependentResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar dependente por ID",
    description="Retorna um dependente específico do usuário logado.",
)
def get_dependent(
    dependent_id: str,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DependentResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")


@router.put(
    "/{dependent_id}",
    response_model=DependentResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dependente",
    description="Atualiza os dados de um dependente do usuário logado.",
)
def update_dependent(
    dependent_id: str,
    body: DependentUpdate,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DependentResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")


@router.delete(
    "/{dependent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir dependente",
    description="Remove um dependente do perfil do usuário logado.",
)
def delete_dependent(
    dependent_id: str,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")
