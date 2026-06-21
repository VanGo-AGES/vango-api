"""US18-TK02 — Implementação do repositório de tokens de recuperação."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.domains.users.reset_token_entity import PasswordResetTokenModel
from src.domains.users.reset_token_repository import IPasswordResetTokenRepository


class PasswordResetTokenRepositoryImpl(IPasswordResetTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US18-TK02
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> PasswordResetTokenModel:
        token = PasswordResetTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        self.session.flush()
        return token

    # US18-TK02
    def find_valid(self, token_hash: str) -> PasswordResetTokenModel | None:
        now = datetime.now(UTC)
        return (
            self.session.query(PasswordResetTokenModel)
            .filter(
                and_(
                    PasswordResetTokenModel.token_hash == token_hash,
                    PasswordResetTokenModel.expires_at > now,
                    PasswordResetTokenModel.used_at.is_(None),
                )
            )
            .first()
        )

    # US18-TK02
    def mark_used(self, token_id: UUID) -> None:
        token = self.session.query(PasswordResetTokenModel).filter_by(id=token_id).first()
        if token:
            token.used_at = datetime.now(UTC)
            self.session.flush()
