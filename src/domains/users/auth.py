"""US17 — Contratos de autenticação (token service).

A implementação concreta (PyJWT) fica em
`src/infrastructure/auth/jwt_token_service.py`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TokenPayload:
    """Conteúdo decodificado de um access token."""

    sub: UUID  # user_id
    role: str
    jti: str  # id único do token (usado pela denylist da US19)
    exp: datetime


class ITokenService(ABC):
    # US17-TK01
    @abstractmethod
    def create_access_token(self, user_id: UUID, role: str, jti: str | None = None) -> str:
        """Emite um JWT assinado para o usuário."""
        ...

    # US17-TK01
    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload:
        """Decodifica/valida o JWT. Levanta erro de domínio se inválido/expirado."""
        ...
