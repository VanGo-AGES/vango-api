"""US17/US18/US19/US20 — Erros do fluxo de autenticação.

US00-TK16 — herdam de DomainError com code/status_code, para que o handler
global responda sem try/except nos controllers.
"""

from src.shared.errors import DomainError


class InvalidTokenError(DomainError):
    code = "invalid_token"
    status_code = 401

    def __init__(self, message: str = "Token inválido ou expirado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class RevokedTokenError(DomainError):
    code = "revoked_token"
    status_code = 401

    def __init__(self, message: str = "Token revogado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class InvalidResetTokenError(DomainError):
    code = "invalid_reset_token"
    status_code = 400

    def __init__(self, message: str = "Token de recuperação inválido, expirado ou já utilizado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class AccountInactiveError(DomainError):
    code = "account_inactive"
    status_code = 401

    def __init__(self, message: str = "Conta inativa.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class DeletionNotConfirmedError(DomainError):
    code = "deletion_not_confirmed"
    status_code = 400

    def __init__(self, message: str = "A exclusão da conta precisa ser confirmada.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


# US17-TK07 — autorização por papel
class ForbiddenRoleError(DomainError):
    code = "forbidden_role"
    status_code = 403

    def __init__(self, message: str = "Acesso negado para o papel do usuário.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


# US17-TK09 — refresh token
class InvalidRefreshTokenError(DomainError):
    code = "invalid_refresh_token"
    status_code = 401

    def __init__(self, message: str = "Refresh token inválido, expirado ou revogado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
