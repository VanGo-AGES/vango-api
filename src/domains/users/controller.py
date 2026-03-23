from typing import Annotated

from fastapi import APIRouter, Depends, status

from .dependencies import get_user_service
from .dtos import UserCreate, UserResponse
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
    return service.create_user(body)
