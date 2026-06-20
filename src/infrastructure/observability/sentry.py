"""US00-TK21 — Sentry error tracking for the FastAPI backend."""

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from src.config import Settings

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "x-api-key",
    "email",
    "phone",
    "cpf",
    "cnpj",
}
REDACTED = "[Filtered]"


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return normalized in SENSITIVE_KEYS or any(part in normalized for part in ("password", "secret", "token"))


def _redact_pii(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: REDACTED if _is_sensitive_key(key) else _redact_pii(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_pii(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_pii(item) for item in value)
    return value


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Remove sensitive request data before Sentry receives the event."""
    request = event.get("request")
    if isinstance(request, dict):
        if "cookies" in request:
            request["cookies"] = REDACTED
        for key in ("headers", "data", "env"):
            if key in request:
                request[key] = _redact_pii(request[key])

    if "extra" in event:
        event["extra"] = _redact_pii(event["extra"])

    return event


def init_sentry(settings: Settings) -> bool:
    """Initialize Sentry only when SENTRY_DSN is configured."""
    if not settings.sentry_dsn:
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        send_default_pii=False,
        environment=settings.sentry_environment,
        release=settings.git_commit,
        before_send=before_send,
    )
    return True
