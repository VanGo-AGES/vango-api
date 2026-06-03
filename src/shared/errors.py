"""US00-TK15 — Base de erros de domínio.

`DomainError` carrega o suficiente para o exception handler global montar uma
resposta HTTP padronizada (status + corpo). Os erros específicos de cada
domínio passarão a herdar desta base, com `code`/`status_code` próprios.
"""


class DomainError(Exception):
    """Erro de domínio mapeável para HTTP pelo handler global (US00-TK15).

    Atributos esperados na implementação:
    - code: str            — código estável legível por máquina (ex.: "user_not_found")
    - status_code: int     — status HTTP correspondente
    - message: str         — mensagem amigável
    - details: dict | None — contexto adicional opcional
    """

    code: str = "domain_error"
    status_code: int = 400

    def __init__(self, message: str | None = None, details: dict | None = None) -> None:
        self.message = message or self.__class__.__name__
        self.details = details
        super().__init__(self.message)
