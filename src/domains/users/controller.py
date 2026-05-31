from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.domains.notifications.service import INotificationService
from src.infrastructure.dependencies.notification_dependencies import get_notification_service
from src.infrastructure.dependencies.user_dependencies import get_user_service

from .dtos import (
    LoginRequest,
    RegisterPushTokenRequest,
    SendTestNotificationRequest,
    SendTestNotificationResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from .errors import DuplicateEmailError, InvalidCredentialsError, UserNotFoundError
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


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Login intermediário (email + senha)",
    description=(
        "Valida e-mail e senha. Retorna o UserResponse em sucesso. "
        "404 quando o e-mail não está cadastrado, 401 quando a senha está incorreta. "
        "Sem emissão de token — autenticação completa será adicionada em US futura."
    ),
)
def login_user(
    body: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        return service.login(body.email, body.password)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos os usuários",
    description="Retorna a lista de todos os usuários cadastrados.",
)
def list_users(service: Annotated[UserService, Depends(get_user_service)]) -> list[UserResponse]:
    return service.list_users()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar usuário por ID",
    description="Retorna os dados de um usuário específico pelo seu ID.",
)
def get_user(user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]) -> UserResponse:
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
    user_id: UUID,
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
def delete_user(user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]) -> None:
    try:
        service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# US12-TK02
@router.post(
    "/me/push-token",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar FCM push token do dispositivo",
    description=(
        "Associa o token FCM do dispositivo ao usuário autenticado. "
        "Usado pelo app mobile logo após o login para habilitar notificações push. "
        "404 se o usuário não existir."
    ),
)
def register_push_token(
    body: RegisterPushTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    x_user_id: Annotated[UUID, Header(alias="X-User-Id")],
) -> UserResponse:
    try:
        return service.register_push_token(x_user_id, body)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/me/send-test-notification",
    response_model=SendTestNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar notificação de teste para o usuário logado",
    description=(
        "Helper de teste: envia um push para o push_token do usuário autenticado, "
        "para validar o pipeline FCM ponta a ponta sem disparar um evento real. "
        "Body é opcional (title/body têm default). "
        "404 se o usuário não existir, 400 se não houver push_token registrado, "
        "502 se o FCM rejeitar o envio."
    ),
)
def send_test_notification(
    service: Annotated[UserService, Depends(get_user_service)],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
    x_user_id: Annotated[UUID, Header(alias="X-User-Id")],
    body: SendTestNotificationRequest | None = None,
) -> SendTestNotificationResponse:
    payload = body or SendTestNotificationRequest()

    try:
        user = service.get_user(x_user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if not user.push_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui push_token registrado. Abra o app logado para registrar o token.",
        )

    try:
        message_id = notification_service.send_test_notification(user.push_token, payload.title, payload.body)
    except Exception as exc:  # noqa: BLE001 — reporta qualquer falha de envio FCM ao chamador
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao enviar push via FCM: {exc}",
        ) from exc

    return SendTestNotificationResponse(
        success=True,
        message_id=str(message_id),
        detail="Notificação de teste enviada com sucesso.",
    )
