"""US17-TK01 — Implementação do token service com PyJWT."""

from uuid import UUID

from src.domains.users.auth import ITokenService, TokenPayload


class JwtTokenService(ITokenService):
    def __init__(self, secret: str, algorithm: str = "HS256", expire_minutes: int = 60) -> None:
        self.secret = secret
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    # US17-TK01
    def create_access_token(self, user_id: UUID, role: str, jti: str | None = None) -> str:
        raise NotImplementedError("US17-TK01")

    # US17-TK01
    def decode_token(self, token: str) -> TokenPayload:
        raise NotImplementedError("US17-TK01")
