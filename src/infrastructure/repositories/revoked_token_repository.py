"""US19-TK01 — Implementação do repositório de denylist de tokens."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.revoked_token_entity import RevokedTokenModel
from src.domains.users.revoked_token_repository import IRevokedTokenRepository


class RevokedTokenRepositoryImpl(IRevokedTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def revoke(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        existing = self.session.get(RevokedTokenModel, jti)
        if existing is None:
            self.session.add(RevokedTokenModel(jti=jti, user_id=user_id, expires_at=expires_at))
            self.session.flush()

    def is_revoked(self, jti: str) -> bool:
        return self.session.get(RevokedTokenModel, jti) is not None
