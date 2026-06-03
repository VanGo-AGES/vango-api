"""US00-TK15 — Exception handler global + ErrorResponse.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US00-TK15")/d' tests/test_shared/test_error_handler.py

O teste monta um app isolado, registra os handlers e dispara um DomainError,
validando o status e o corpo padronizado (com `detail` preservado).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.error_handler import register_exception_handlers
from src.shared.errors import DomainError


class _SampleError(DomainError):
    code = "sample_error"
    status_code = 418


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():  # noqa: ANN202
        raise _SampleError("algo deu errado", details={"field": "x"})

    return app


@pytest.mark.skip(reason="US00-TK15")
def test_domain_error_mapped_to_status_and_body():
    client = TestClient(_build_app(), raise_server_exceptions=False)
    resp = client.get("/boom")

    assert resp.status_code == 418
    body = resp.json()
    # campo legado preservado para o FE
    assert body["detail"] == "algo deu errado"
    # campos estruturados novos
    assert body["code"] == "sample_error"
    assert body["message"] == "algo deu errado"
    assert body["details"] == {"field": "x"}
    assert "trace_id" in body


@pytest.mark.skip(reason="US00-TK15")
def test_domain_error_default_status():
    assert DomainError.status_code == 400
    assert DomainError("x").message == "x"
