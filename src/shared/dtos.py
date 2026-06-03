"""US00-TK15 — DTO de resposta de erro padronizada.

Mantém o campo `detail` (compatibilidade com o FE e com os testes existentes)
e adiciona os campos estruturados.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Corpo padronizado retornado em respostas 4xx/5xx (US00-TK15)."""

    detail: str
    code: str
    message: str
    details: dict | None = None
    trace_id: str | None = None
