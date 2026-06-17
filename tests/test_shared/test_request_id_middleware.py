"""US00-TK17 — Middleware de correlation/request id.

Remova o skip rodando:
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.middleware.request_id import RequestIdMiddleware, get_request_id


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    def ping():  # noqa: ANN202
        return {"request_id": get_request_id()}

    return app


def test_generates_request_id_when_absent():
    client = TestClient(_build_app())
    resp = client.get("/ping")

    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id")
    # o id exposto no contexto deve bater com o header
    assert resp.json()["request_id"] == resp.headers["X-Request-Id"]


def test_propagates_incoming_request_id():
    client = TestClient(_build_app())
    resp = client.get("/ping", headers={"X-Request-Id": "abc-123"})

    assert resp.headers["X-Request-Id"] == "abc-123"
    assert resp.json()["request_id"] == "abc-123"


def test_sets_sentry_tags_for_request_id(mocker):
    set_tag = mocker.patch("src.infrastructure.middleware.request_id.sentry_sdk.set_tag")
    client = TestClient(_build_app())

    resp = client.get("/ping", headers={"X-Request-Id": "req-123"})

    assert resp.status_code == 200
    set_tag.assert_any_call("request_id", "req-123")
    set_tag.assert_any_call("trace_id", "req-123")
