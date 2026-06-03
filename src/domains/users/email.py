"""US18-TK01 — Contrato de serviço de e-mail.

Implementação concreta (SMTP/SES) em `src/infrastructure/email/`.
"""

from abc import ABC, abstractmethod


class IEmailService(ABC):
    # US18-TK01
    @abstractmethod
    def send(self, to: str, subject: str, body_html: str, body_text: str | None = None) -> None:
        """Envia um e-mail. Levanta exceção em falha de transporte."""
        ...
