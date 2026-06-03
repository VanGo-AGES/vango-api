"""Épico 5 — AuthService.

Orquestra os fluxos de autenticação:
- login (US17-TK03): valida credenciais e emite JWT.
- request_password_reset / reset_password (US18-TK04).
- logout (US19-TK02): revoga o jti atual.
- delete_account (US20-TK04): soft delete + anonimização + revogação.

Recebe as dependências por injeção (mockadas nos testes de service).
"""

from uuid import UUID

from src.domains.users.auth import ITokenService, TokenPayload
from src.domains.users.dtos import LoginResponse
from src.domains.users.email import IEmailService
from src.domains.users.repository import IPasswordHasher, IUserRepository
from src.domains.users.reset_token_repository import IPasswordResetTokenRepository
from src.domains.users.revoked_token_repository import IRevokedTokenRepository


class AuthService:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        reset_token_repository: IPasswordResetTokenRepository,
        email_service: IEmailService,
        revoked_token_repository: IRevokedTokenRepository,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.reset_token_repository = reset_token_repository
        self.email_service = email_service
        self.revoked_token_repository = revoked_token_repository

    # US17-TK03
    def login(self, email: str, password: str) -> LoginResponse:
        """Valida credenciais (bloqueia conta inativa) e emite o access token."""
        raise NotImplementedError("US17-TK03")

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
        raise NotImplementedError("US19-TK02")

    # US20-TK04
    def delete_account(self, user_id: UUID, confirm: bool) -> None:
        """Exige confirmação, faz soft delete + anonimização e revoga tokens."""
        raise NotImplementedError("US20-TK04")
