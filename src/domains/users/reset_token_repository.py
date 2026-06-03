"""US18-TK02 — Interface do repositório de tokens de recuperação."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domains.users.reset_token_entity import PasswordResetTokenModel


class IPasswordResetTokenRepository(ABC):
    # US18-TK02
    @abstractmethod
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> PasswordResetTokenModel: ...

    # US18-TK02
    @abstractmethod
    def find_valid(self, token_hash: str) -> PasswordResetTokenModel | None:
        """Retorna o token se existir, não expirado e não usado; senão None."""
        ...

    # US18-TK02
    @abstractmethod
    def mark_used(self, token_id: UUID) -> None: ...
