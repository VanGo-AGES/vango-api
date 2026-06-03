"""US17-TK01 — Implementação do token service com PyJWT."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError

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
            jti = uuid4().hex

        now = datetime.now(UTC)
        expiration = now + timedelta(minutes=self.expire_minutes)

        payload = {
            "sub": str(user_id),
            "role": role,
            "jti": jti,
            "exp": expiration,
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    # US17-TK01
    def decode_token(self, token: str) -> TokenPayload:
        try:
            decoded = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"require": ["exp", "sub", "jti"]},
            )
        except PyJWTInvalidTokenError as exc:
            raise InvalidTokenError() from exc

        try:
            subject = UUID(decoded["sub"])
        except Exception as exc:
            raise InvalidTokenError() from exc

        role = decoded.get("role")
        jti = decoded.get("jti")
        exp = decoded.get("exp")

        if role is None or jti is None or exp is None:
            raise InvalidTokenError()

        try:
            expiration = datetime.fromtimestamp(exp, UTC) if isinstance(exp, (int, float)) else datetime.fromtimestamp(int(exp), UTC)
        except Exception as exc:
            raise InvalidTokenError() from exc

        return TokenPayload(sub=subject, role=role, jti=jti, exp=expiration)
