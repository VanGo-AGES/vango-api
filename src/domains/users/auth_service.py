"""Épico 5 — AuthService.

Orquestra os fluxos de autenticação:
- login (US17-TK03): valida credenciais e emite JWT.
- request_password_reset / reset_password (US18-TK04).
- logout (US19-TK02): revoga o jti atual.
- delete_account (US20-TK04): soft delete + anonimização + revogação.

Recebe as dependências por injeção (mockadas nos testes de service).
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.domains.users.auth import ITokenService, TokenPayload
from src.domains.users.auth_errors import (
    AccountInactiveError,
    DeletionNotConfirmedError,
    InvalidRefreshTokenError,
)
from src.domains.users.dtos import LoginResponse, UserResponse
from src.domains.users.email import IEmailService
from src.domains.users.errors import InvalidCredentialsError, UserNotFoundError
from src.domains.users.refresh_token_repository import IRefreshTokenRepository
from src.domains.users.repository import IPasswordHasher, IUserRepository
from src.domains.users.reset_token_repository import IPasswordResetTokenRepository
from src.domains.users.revoked_token_repository import IRevokedTokenRepository

_REFRESH_TOKEN_TTL_DAYS = 30


class AuthService:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        reset_token_repository: IPasswordResetTokenRepository,
        email_service: IEmailService,
        revoked_token_repository: IRevokedTokenRepository,
        refresh_token_repository: IRefreshTokenRepository | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.reset_token_repository = reset_token_repository
        self.email_service = email_service
        self.revoked_token_repository = revoked_token_repository
        self.refresh_token_repository = refresh_token_repository

    # US17-TK03 (refresh emitido na US17-TK09 quando o refresh_token_repository está presente)
    def login(self, email: str, password: str) -> LoginResponse:
        """Valida credenciais (bloqueia conta inativa) e emite o access token
        (e o refresh token, quando o fluxo de refresh está ativo)."""
        user = self.user_repository.find_by_email(email)
        if user is None:
            raise UserNotFoundError()

        if not self.password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        jti = str(uuid4())
        access_token = self.token_service.create_access_token(user.id, user.role, jti)
        raw_refresh: str | None = None

        if self.refresh_token_repository is not None:
            raw_refresh = self._issue_refresh(user.id)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",  # nosec B106 - tipo de token OAuth, não é senha
            user=UserResponse.model_validate(user),
            refresh_token=raw_refresh,
        )

    # US17-TK09
    def refresh(self, refresh_token: str) -> LoginResponse:
        """Valida o refresh token, rotaciona (emite novo par e revoga o usado)
        e retorna o novo LoginResponse. Erro de domínio se inválido/expirado/revogado.
        """
        if self.refresh_token_repository is None:
            raise InvalidRefreshTokenError()

        token_hash = self._hash(refresh_token)
        record = self.refresh_token_repository.find_valid(token_hash)
        if record is None:
            raise InvalidRefreshTokenError()

        user = self.user_repository.find_by_id(record.user_id)
        jti = str(uuid4())
        access_token = self.token_service.create_access_token(user.id, user.role, jti)

        self.refresh_token_repository.revoke(record.id)
        new_raw = self._issue_refresh(user.id)

        return LoginResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
            refresh_token=new_raw,
        )

    def _hash(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    def _issue_refresh(self, user_id: UUID) -> str:
        raw = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=_REFRESH_TOKEN_TTL_DAYS)
        self.refresh_token_repository.create(user_id, self._hash(raw), expires_at)
        return raw

    # US18-TK04
    def request_password_reset(self, email: str) -> None:
        """Gera token, persiste o hash e dispara o e-mail. Resposta neutra
        (não revela se o e-mail existe).
        """
        raise NotImplementedError("US18-TK04")

    # US18-TK04
    def reset_password(self, token: str, new_password: str) -> None:
        """Valida o token, aplica as regras de senha, troca o hash, marca o
        token como usado e revoga sessões ativas.
        """
        raise NotImplementedError("US18-TK04")

    # US19-TK02
    def logout(self, token_payload: TokenPayload) -> None:
        """Revoga o jti atual até o seu exp."""
        jti = token_payload.jti
        user_id = token_payload.sub
        expires_at = token_payload.exp

        self.revoked_token_repository.revoke(jti=jti, user_id=user_id, expires_at=expires_at)

    # US20-TK04
    def delete_account(self, user_id: UUID, confirm: bool) -> None:
        """Exige confirmação, faz soft delete + anonimização e encerra a sessão via inativação."""
        if not confirm:
            raise DeletionNotConfirmedError()

        deleted = self.user_repository.soft_delete_and_anonymize(user_id)
        if not deleted:
            raise UserNotFoundError()
