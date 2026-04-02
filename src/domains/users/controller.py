from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.infrastructure.dependencies.user_dependencies import get_user_service

from .dtos import UserCreate, UserResponse, UserUpdate
from .errors import DuplicateEmailError, UserNotFoundError
from .service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar um novo usuário",
    description="Cria um usuário no banco e retorna os dados sem a senha.",
)
def register_user(body: UserCreate, service: Annotated[UserService, Depends(get_user_service)]) -> UserResponse:
    """
    Endpoint para cadastrar motoristas, passageiros ou responsáveis.
    """
    try:
        return service.create_user(body)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar usuário por ID",
    description="Retorna os dados de um usuário específico pelo seu ID.",
)
def get_user(user_id: str, service: Annotated[UserService, Depends(get_user_service)]) -> UserResponse:
    try:
        return service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar usuário",
    description="Atualiza os campos de um usuário existente.",
)
def update_user(
    user_id: str,
    body: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        return service.update_user(user_id, body)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário",
    description="Remove a conta do usuário e todos os dados associados em cascata.",
)
def delete_user(user_id: str, service: Annotated[UserService, Depends(get_user_service)]) -> None:
    try:
        service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
