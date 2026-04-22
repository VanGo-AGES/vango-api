"""US07 — Erros do domínio stops."""


class StopNotFoundError(Exception):
    """Erro levantado quando uma parada (stop) não é encontrada."""

    def __init__(self, message: str = "Parada não encontrada."):
        super().__init__(message)
        self.message = message
