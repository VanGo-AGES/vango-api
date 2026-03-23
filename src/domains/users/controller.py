from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.infrastructure.dependencies.user_dependencies import get_user_service

from .dtos import UserCreate, UserResponse
from .errors import DuplicateEmailError
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
