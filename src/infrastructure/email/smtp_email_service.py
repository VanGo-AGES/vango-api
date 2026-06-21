"""US18-TK01 — Implementação SMTP/SES do serviço de e-mail.

Usa `smtplib` da stdlib (sem dependência nova). As credenciais vêm do
`config.py`/secrets. Os testes mockam o transporte — não enviam e-mail real.
"""

import smtplib
from email.message import EmailMessage

from loguru import logger

from src.domains.users.email import IEmailService
from src.infrastructure.middleware.request_id import get_request_id


class SmtpEmailService(IEmailService):
    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    # US18-TK01
    def send(self, to: str, subject: str, body_html: str, body_text: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject

        if body_text:
            msg.set_content(body_text)
            msg.add_alternative(body_html, subtype="html")
        else:
            msg.set_content(body_html, subtype="html")

        try:
            with smtplib.SMTP(self.host, self.port) as smtp:
                smtp.starttls()
                smtp.login(self.username, self.password)
                smtp.send_message(msg)
        except Exception:
            request_id = get_request_id()
            logger.bind(request_id=request_id, trace_id=request_id).exception(
                "SMTP email send failed",
                host=self.host,
                port=self.port,
                sender=self.sender,
                recipient=to,
                subject=subject,
            )
            raise
