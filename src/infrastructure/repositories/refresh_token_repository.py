"""US17-TK08 — Implementação do repositório de refresh tokens."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.refresh_token_entity import RefreshTokenModel
from src.domains.users.refresh_token_repository import IRefreshTokenRepository


class RefreshTokenRepositoryImpl(IRefreshTokenRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US17-TK08
    def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> RefreshTokenModel:
        raise NotImplementedError("US17-TK08")

    # US17-TK08
    def find_valid(self, token_hash: str) -> RefreshTokenModel | None:
        raise NotImplementedError("US17-TK08")

    # US17-TK08
    def revoke(self, token_id: UUID) -> None:
        raise NotImplementedError("US17-TK08")

    # US17-TK08
    def revoke_all_for_user(self, user_id: UUID) -> int:
        raise NotImplementedError("US17-TK08")
