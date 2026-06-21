"""US16-TK01 — Regras de senha reutilizáveis.

Usado pelo `UserCreate`/`UserUpdate` (cadastro/troca) e pelo fluxo de reset
(US18). Centraliza a política para não duplicar regra.
"""

import re

MIN_LENGTH = 8


class WeakPasswordError(ValueError):
    """Senha não atende às regras mínimas (vira 422 na borda HTTP)."""


# US16-TK01
def validate_password(password: str) -> str:
    """Valida a senha contra a política definida.

    Regras esperadas: comprimento mínimo (>= 8), ao menos uma letra maiúscula,
    uma minúscula, um dígito e um caractere especial. Levanta `WeakPasswordError`
    com mensagem específica quando alguma regra falha; retorna a senha quando ok.
    """
    if len(password) < MIN_LENGTH:
        raise WeakPasswordError(f"A senha deve ter no mínimo {MIN_LENGTH} caracteres.")
    if not re.search(r"[A-Z]", password):
        raise WeakPasswordError("A senha deve conter ao menos uma letra maiúscula.")
    if not re.search(r"[a-z]", password):
        raise WeakPasswordError("A senha deve conter ao menos uma letra minúscula.")
    if not re.search(r"\d", password):
        raise WeakPasswordError("A senha deve conter ao menos um dígito.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise WeakPasswordError("A senha deve conter ao menos um caractere especial.")
    return password
