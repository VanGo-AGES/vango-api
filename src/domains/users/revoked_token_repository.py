"""US19-TK01 — Interface do repositório de denylist de tokens."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class IRevokedTokenRepository(ABC):
    # US19-TK01
    @abstractmethod
    def revoke(self, jti: str, user_id: UUID, expires_at: datetime) -> None: ...

    # US19-TK01
    @abstractmethod
    def is_revoked(self, jti: str) -> bool: ...
