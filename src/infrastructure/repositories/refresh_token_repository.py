"""US17-TK08 — Implementação do repositório de refresh tokens."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.domains.users.refresh_token_entity import RefreshTokenModel
from src.domains.users.refresh_token_repository import IRefreshTokenRepository


class RefreshTokenRepositoryImpl(IRefreshTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US17-TK08
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> RefreshTokenModel:
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        self.session.flush()
        return token

    # US17-TK08
    def find_valid(self, token_hash: str) -> RefreshTokenModel | None:
        now = datetime.now(UTC)
        return (
            self.session.query(RefreshTokenModel)
            .filter(
                and_(
                    RefreshTokenModel.token_hash == token_hash,
                    RefreshTokenModel.expires_at > now,
                    RefreshTokenModel.revoked_at.is_(None),
                )
            )
            .first()
        )

    # US17-TK08
    def revoke(self, token_id: UUID) -> None:
        token = self.session.get(RefreshTokenModel, token_id)
        if token is not None and token.revoked_at is None:
            token.revoked_at = datetime.now(UTC)
            self.session.flush()

    # US17-TK08
    def revoke_all_for_user(self, user_id: UUID) -> int:
        now = datetime.now(UTC)
        updated_count = (
            self.session.query(RefreshTokenModel)
            .filter(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
                RefreshTokenModel.expires_at > now,
            )
            .update({RefreshTokenModel.revoked_at: now}, synchronize_session="fetch")
        )
        self.session.flush()
        return int(updated_count)
