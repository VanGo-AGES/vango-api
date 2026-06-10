"""Épico 5 — Wiring das dependências de autenticação.

Fornece o token service, os repositórios de denylist/reset, o serviço de
e-mail, o AuthService e a dependência real `get_current_user` (JWT).
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.config import settings
from src.domains.users.auth import ITokenService, TokenPayload
from src.domains.users.auth_service import AuthService
from src.domains.users.email import IEmailService
from src.domains.users.entity import UserModel
from src.domains.users.refresh_token_repository import IRefreshTokenRepository
from src.domains.users.repository import IPasswordHasher, IUserRepository
from src.domains.users.reset_token_repository import IPasswordResetTokenRepository
from src.domains.users.revoked_token_repository import IRevokedTokenRepository
from src.infrastructure.auth.jwt_token_service import JwtTokenService
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.user_dependencies import get_password_hasher, get_user_repository
from src.infrastructure.email.smtp_email_service import SmtpEmailService
from src.infrastructure.repositories.password_reset_token_repository import PasswordResetTokenRepositoryImpl
from src.infrastructure.repositories.refresh_token_repository import RefreshTokenRepositoryImpl
from src.infrastructure.repositories.revoked_token_repository import RevokedTokenRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_token_service() -> ITokenService:
    return JwtTokenService(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_reset_token_repository(db: DatabaseSession) -> IPasswordResetTokenRepository:
    return PasswordResetTokenRepositoryImpl(db)


def get_revoked_token_repository(db: DatabaseSession) -> IRevokedTokenRepository:
    return RevokedTokenRepositoryImpl(db)


def get_refresh_token_repository(db: DatabaseSession) -> IRefreshTokenRepository:
    return RefreshTokenRepositoryImpl(db)


def get_email_service() -> IEmailService:
    return SmtpEmailService(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.smtp_from,
    )


def get_auth_service(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
    reset_repo: Annotated[IPasswordResetTokenRepository, Depends(get_reset_token_repository)],
    email_service: Annotated[IEmailService, Depends(get_email_service)],
    revoked_repo: Annotated[IRevokedTokenRepository, Depends(get_revoked_token_repository)],
    refresh_repo: Annotated[IRefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> AuthService:
    return AuthService(
        user_repository=user_repo,
        password_hasher=password_hasher,
        token_service=token_service,
        reset_token_repository=reset_repo,
        email_service=email_service,
        revoked_token_repository=revoked_repo,
        refresh_token_repository=refresh_repo,
    )


# US17-TK02 — payload do token autenticado (Bearer)
def get_current_token_payload(
    token_service: Annotated[ITokenService, Depends(get_token_service)],
    revoked_repo: Annotated[IRevokedTokenRepository, Depends(get_revoked_token_repository)],
    authorization: Annotated[str | None, Header()] = None,
) -> TokenPayload:
    """Extrai e valida o Bearer token; checa a denylist (US19). 401 se inválido."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        payload = token_service.decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if revoked_repo.is_revoked(payload.jti):
        raise HTTPException(status_code=401, detail="Token revoked")

    return payload


# US17-TK02 — usuário autenticado
def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_current_token_payload)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UserModel:
    """Carrega o usuário do token. 401 se não existir/estiver inativo."""
    user = user_repo.find_by_id(payload.sub)
    if user is None or not getattr(user, "is_active", False):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# US17-TK07 — autorização por papel (motorista)
def get_current_driver(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    """Garante que o usuário autenticado é motorista. 403 caso contrário."""
    raise NotImplementedError("US17-TK07")
