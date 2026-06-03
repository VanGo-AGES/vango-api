"""US17/US18/US19 — Erros do fluxo de autenticação.

Seguem o padrão atual (subclasses de Exception). Na US00-TK16 passarão a
herdar de DomainError com code/status_code.
"""


class InvalidTokenError(Exception):
    def __init__(self, message: str = "Token inválido ou expirado."):
        super().__init__(message)


class RevokedTokenError(Exception):
    def __init__(self, message: str = "Token revogado."):
        super().__init__(message)


class InvalidResetTokenError(Exception):
    def __init__(self, message: str = "Token de recuperação inválido, expirado ou já utilizado."):
        super().__init__(message)


class AccountInactiveError(Exception):
    def __init__(self, message: str = "Conta inativa."):
        super().__init__(message)


class DeletionNotConfirmedError(Exception):
    def __init__(self, message: str = "A exclusão da conta precisa ser confirmada."):
        super().__init__(message)


# US17-TK07 — autorização por papel
class ForbiddenRoleError(Exception):
    def __init__(self, message: str = "Acesso negado para o papel do usuário."):
        super().__init__(message)


# US17-TK09 — refresh token
class InvalidRefreshTokenError(Exception):
    def __init__(self, message: str = "Refresh token inválido, expirado ou revogado."):
        super().__init__(message)
