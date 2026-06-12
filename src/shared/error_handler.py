"""US00-TK15 — Registro do exception handler global.

`register_exception_handlers(app)` registra o handler que converte
`DomainError` (e subclasses) na resposta padronizada `ErrorResponse`,
preenchendo `trace_id` a partir do correlation id da request (US00-TK17).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.infrastructure.middleware.request_id import get_request_id
from src.shared.dtos import ErrorResponse
from src.shared.errors import DomainError


# US00-TK15
def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro no app FastAPI."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        response = ErrorResponse(
            detail=exc.message,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            trace_id=get_request_id(),
        )
        return JSONResponse(status_code=exc.status_code, content=response.dict())
