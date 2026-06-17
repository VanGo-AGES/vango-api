from src.config import Settings
from src.infrastructure.observability.sentry import REDACTED, before_send, init_sentry
from src.infrastructure.observability import sentry as sentry_observability


def _settings(sentry_dsn: str = "") -> Settings:
    return Settings(
        DATABASE_URL="sqlite:///test.db",
        SENTRY_DSN=sentry_dsn,
        SENTRY_ENVIRONMENT="staging",
        GIT_COMMIT="abc123",
    )


def test_init_sentry_skips_when_dsn_is_empty(mocker):
    init = mocker.patch.object(sentry_observability.sentry_sdk, "init")

    assert init_sentry(_settings()) is False

    init.assert_not_called()


def test_init_sentry_uses_dsn_environment_release_and_disables_default_pii(mocker):
    init = mocker.patch.object(sentry_observability.sentry_sdk, "init")

    assert init_sentry(_settings("https://public@example.ingest.sentry.io/1")) is True

    kwargs = init.call_args.kwargs
    assert kwargs["dsn"] == "https://public@example.ingest.sentry.io/1"
    assert kwargs["environment"] == "staging"
    assert kwargs["release"] == "abc123"
    assert kwargs["send_default_pii"] is False
    assert kwargs["before_send"] is before_send
    assert kwargs["integrations"]


def test_before_send_redacts_sensitive_request_data():
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer secret",
                "X-Request-Id": "req-123",
            },
            "cookies": {"session": "secret-cookie"},
            "data": {
                "email": "person@example.com",
                "password": "secret",
                "nested": {"refresh_token": "token"},
            },
        },
        "extra": {"api_key": "secret-key", "safe": "value"},
    }

    filtered = before_send(event, {})

    assert filtered is event
    assert event["request"]["headers"]["Authorization"] == REDACTED
    assert event["request"]["headers"]["X-Request-Id"] == "req-123"
    assert event["request"]["cookies"] == REDACTED
    assert event["request"]["data"]["email"] == REDACTED
    assert event["request"]["data"]["password"] == REDACTED
    assert event["request"]["data"]["nested"]["refresh_token"] == REDACTED
    assert event["extra"]["api_key"] == REDACTED
    assert event["extra"]["safe"] == "value"
