"""US18-TK01 — SmtpEmailService.

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US18-TK01")/d' tests/test_auth/test_email_service.py

Mocka o transporte SMTP — não envia e-mail real.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.email.smtp_email_service import SmtpEmailService


def _service():
    return SmtpEmailService(host="smtp.test", port=587, username="u", password="p", sender="no-reply@vango.app")


@pytest.mark.skip(reason="US18-TK01")
def test_send_uses_smtp_transport():
    with patch("smtplib.SMTP") as smtp_cls:
        instance = MagicMock()
        smtp_cls.return_value.__enter__.return_value = instance

        _service().send(to="user@b.com", subject="Reset", body_html="<b>hi</b>", body_text="hi")

        assert smtp_cls.called
        assert instance.send_message.called or instance.sendmail.called


@pytest.mark.skip(reason="US18-TK01")
def test_send_propagates_transport_failure():
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        with pytest.raises(OSError):
            _service().send(to="user@b.com", subject="x", body_html="x")


@pytest.mark.skip(reason="US18-TK01")
def test_send_addresses_message_correctly():
    """A mensagem precisa ir para o destinatário certo, com subject e remetente."""
    with patch("smtplib.SMTP") as smtp_cls:
        instance = MagicMock()
        smtp_cls.return_value.__enter__.return_value = instance

        _service().send(to="user@b.com", subject="Recuperar senha", body_html="<b>hi</b>", body_text="hi")

        assert instance.send_message.called
        msg = instance.send_message.call_args.args[0]
        assert msg["To"] == "user@b.com"
        assert msg["Subject"] == "Recuperar senha"
        assert msg["From"] == "no-reply@vango.app"


@pytest.mark.skip(reason="US18-TK01")
def test_send_authenticates_with_credentials():
    with patch("smtplib.SMTP") as smtp_cls:
        instance = MagicMock()
        smtp_cls.return_value.__enter__.return_value = instance

        _service().send(to="user@b.com", subject="x", body_html="x")

        instance.login.assert_called_once_with("u", "p")
