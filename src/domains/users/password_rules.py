"""US16-TK01 — Regras de senha reutilizáveis.

Usado pelo `UserCreate`/`UserUpdate` (cadastro/troca) e pelo fluxo de reset
(US18). Centraliza a política para não duplicar regra.
"""


class WeakPasswordError(ValueError):
    """Senha não atende às regras mínimas (vira 422 na borda HTTP)."""


# US16-TK01
def validate_password(password: str) -> str:
    """Valida a senha contra a política definida.

    Regras esperadas: comprimento mínimo (>= 8), ao menos uma letra maiúscula,
    uma minúscula, um dígito e um caractere especial. Levanta `WeakPasswordError`
    com mensagem específica quando alguma regra falha; retorna a senha quando ok.
    """
    raise NotImplementedError("US16-TK01")
