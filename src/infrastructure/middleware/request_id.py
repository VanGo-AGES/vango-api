"""US00-TK17 — Middleware de correlation/request id + logging estruturado.

Gera (ou propaga) um `X-Request-Id` por request, guarda em contextvar para o
logger e o exception handler usarem como `trace_id`, e loga cada request em
JSON (método, path, status, latência).
"""

import time
import uuid
from contextvars import ContextVar

import sentry_sdk
from loguru import logger
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
        # Obter ou gerar request_id
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Definir no contextvar
        token = request_id_ctx.set(request_id)
        sentry_sdk.set_tag("request_id", request_id)
        sentry_sdk.set_tag("trace_id", request_id)

        try:
            # Marcar início
            start_time = time.perf_counter()

            # Chamar o próximo middleware/handler
            response = await call_next(request)

            # Calcular latência
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Log estruturado
            logger.bind(request_id=request_id).info(
                "HTTP Request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )

            # Adicionar ao header da resposta
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            # Resetar o contextvar
            request_id_ctx.reset(token)
