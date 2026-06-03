"""US00-TK15 — Registro do exception handler global.

`register_exception_handlers(app)` registra o handler que converte
`DomainError` (e subclasses) na resposta padronizada `ErrorResponse`,
preenchendo `trace_id` a partir do correlation id da request (US00-TK17).
"""

from fastapi import FastAPI


# US00-TK15
def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro no app FastAPI."""
    raise NotImplementedError("US00-TK15")
