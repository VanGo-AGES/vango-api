"""US19-TK01 — Implementação do repositório de denylist de tokens."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.revoked_token_repository import IRevokedTokenRepository


class RevokedTokenRepositoryImpl(IRevokedTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US19-TK01
    def revoke(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        raise NotImplementedError("US19-TK01")

    # US19-TK01
    def is_revoked(self, jti: str) -> bool:
        raise NotImplementedError("US19-TK01")
