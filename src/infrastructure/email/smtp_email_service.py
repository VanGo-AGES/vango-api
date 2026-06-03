"""US18-TK01 — Implementação SMTP/SES do serviço de e-mail.

Usa `smtplib` da stdlib (sem dependência nova). As credenciais vêm do
`config.py`/secrets. Os testes mockam o transporte — não enviam e-mail real.
"""

from src.domains.users.email import IEmailService


class SmtpEmailService(IEmailService):
    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    # US18-TK01
    def send(self, to: str, subject: str, body_html: str, body_text: str | None = None) -> None:
        raise NotImplementedError("US18-TK01")
