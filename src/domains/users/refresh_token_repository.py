"""US17-TK08 — Interface do repositório de refresh tokens."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domains.users.refresh_token_entity import RefreshTokenModel


class IRefreshTokenRepository(ABC):
    # US17-TK08
    @abstractmethod
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> RefreshTokenModel: ...

    # US17-TK08
    @abstractmethod
    def find_valid(self, token_hash: str) -> RefreshTokenModel | None:
        """Retorna o refresh token se existir, não expirado e não revogado; senão None."""
        ...

    # US17-TK08
    @abstractmethod
    def revoke(self, token_id: UUID) -> None:
        """Revoga um refresh token específico (usado na rotação)."""
        ...

    # US17-TK08
    @abstractmethod
    def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoga todos os refresh tokens ativos do usuário (logout global / reset / exclusão).
        Retorna a quantidade revogada."""
        ...
