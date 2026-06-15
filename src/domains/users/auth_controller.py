"""Épico 5 — Endpoints de autenticação.

Agrupa login (US17), logout (US19), recuperação de senha (US18) e exclusão de
conta (US20). Login/forgot/reset são públicos; logout e delete exigem auth.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.domains.users.auth import TokenPayload
from src.domains.users.auth_errors import DeletionNotConfirmedError, InvalidRefreshTokenError
from src.domains.users.auth_service import AuthService
from src.domains.users.dtos import (
    DeleteAccountRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordConfirm,
    UserResponse,
)
from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import (
    get_auth_service,
    get_current_token_payload,
    get_current_user,
)

router = APIRouter(tags=["Auth"])


# US17-TK04
@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return service.login(body.email, body.password)


# US17-TK10
@router.post("/auth/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def refresh(
    body: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    try:
        return service.refresh(body.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


# US17-TK06
@router.get("/users/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    return current_user


# US18-TK05
@router.post("/auth/password/forgot", status_code=status.HTTP_200_OK)
def forgot_password(
    body: ForgotPasswordRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    service.request_password_reset(body.email)
    return {"detail": "Se o e-mail existir, enviaremos as instruções de recuperação."}


# US18-TK05
@router.post("/auth/password/reset", status_code=status.HTTP_200_OK)
def reset_password(
    body: ResetPasswordConfirm,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    service.reset_password(body.token, body.new_password)
    return {"detail": "Senha redefinida com sucesso."}


# US19-TK03
@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    service: Annotated[AuthService, Depends(get_auth_service)],
    payload: Annotated[TokenPayload, Depends(get_current_token_payload)],
) -> None:
    service.logout(payload)


# US20-TK05
@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    body: DeleteAccountRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> None:
    try:
        service.delete_account(current_user.id, body.confirm)
    except DeletionNotConfirmedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
