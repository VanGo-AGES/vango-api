from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.infrastructure.dependencies.auth_dependencies import get_current_user
from src.infrastructure.dependencies.dependent_dependencies import get_dependent_service

from .dtos import DependentCreate, DependentResponse, DependentUpdate
from .errors import DependentAccessDeniedError, DependentNotFoundError, DependentOwnershipError
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
    try:
        return service.add_dependent(
            user_id=current_user["id"],
            user_role=current_user["role"],
            data=body,
        )
    except DependentAccessDeniedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


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
    return service.get_dependents(current_user["id"])


@router.get(
    "/{dependent_id}",
    response_model=DependentResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar dependente por ID",
    description="Retorna um dependente específico do usuário logado.",
)
def get_dependent(
    dependent_id: UUID,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DependentResponse:
    try:
        return service.get_dependent(current_user["id"], dependent_id)
    except DependentNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DependentOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.put(
    "/{dependent_id}",
    response_model=DependentResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dependente",
    description="Atualiza os dados de um dependente do usuário logado.",
)
def update_dependent(
    dependent_id: UUID,
    body: DependentUpdate,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DependentResponse:
    try:
        return service.update_dependent(current_user["id"], dependent_id, body)
    except DependentNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DependentOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.delete(
    "/{dependent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir dependente",
    description="Remove um dependente do perfil do usuário logado.",
)
def delete_dependent(
    dependent_id: UUID,
    service: Annotated[DependentService, Depends(get_dependent_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    try:
        service.delete_dependent(current_user["id"], dependent_id)
    except DependentNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DependentOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
