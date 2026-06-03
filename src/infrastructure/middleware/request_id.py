"""US00-TK17 — Middleware de correlation/request id + logging estruturado.

Gera (ou propaga) um `X-Request-Id` por request, guarda em contextvar para o
logger e o exception handler usarem como `trace_id`, e loga cada request em
JSON (método, path, status, latência).
"""

from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# contextvar lido pelo logger e pelo exception handler (US00-TK15/TK18)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Retorna o request id da request atual, se houver."""
    return request_id_ctx.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injeta/propaga o X-Request-Id e loga a request (US00-TK17)."""

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        raise NotImplementedError("US00-TK17")
