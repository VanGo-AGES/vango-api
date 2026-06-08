"""US17-TK01 — Implementação do token service com PyJWT."""

from datetime import datetime, timedelta
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
            jti = uuid4().hex

        payload = {
            "sub": str(user_id),
            "role": role,
            "jti": jti,
            "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes),
        }

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    # US17-TK01
    def decode_token(self, token: str) -> TokenPayload:
        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

        try:
            sub = UUID(decoded["sub"])
            role = str(decoded["role"])
            jti = str(decoded["jti"])
            exp = datetime.fromtimestamp(decoded["exp"])
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidTokenError() from exc

        return TokenPayload(sub=sub, role=role, jti=jti, exp=exp)
