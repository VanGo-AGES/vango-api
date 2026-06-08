"""US17-TK01 — Implementação do token service com PyJWT."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from src.domains.users.auth import ITokenService, TokenPayload
from src.domains.users.auth_errors import InvalidTokenError


class JwtTokenService(ITokenService):
    def __init__(self, secret: str, algorithm: str = "HS256", expire_minutes: int = 60) -> None:
        self.secret = secret
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    # US17-TK01
    def create_access_token(self, user_id: UUID, role: str, jti: str | None = None) -> str:
        if jti is None:
            jti = str(uuid4())

        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self.expire_minutes)

        payload = {
            "sub": str(user_id),
            "role": role,
            "jti": jti,
            "exp": expires_at,
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    # US17-TK01
    def decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        try:
            return TokenPayload(
                sub=UUID(payload["sub"]),
                role=str(payload["role"]),
                jti=str(payload["jti"]),
                exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            )
        except Exception as exc:
            raise InvalidTokenError("Token inválido.") from exc
