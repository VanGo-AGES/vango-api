"""US18-TK02 — Implementação do repositório de tokens de recuperação."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.reset_token_entity import PasswordResetTokenModel
from src.domains.users.reset_token_repository import IPasswordResetTokenRepository


class PasswordResetTokenRepositoryImpl(IPasswordResetTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US18-TK02
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> PasswordResetTokenModel:
        raise NotImplementedError("US18-TK02")

    # US18-TK02
    def find_valid(self, token_hash: str) -> PasswordResetTokenModel | None:
        raise NotImplementedError("US18-TK02")

    # US18-TK02
    def mark_used(self, token_id: UUID) -> None:
        raise NotImplementedError("US18-TK02")
