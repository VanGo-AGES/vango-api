from src.shared.errors import DomainError


class DependentAccessDeniedError(DomainError):
    code = "dependent_access_denied"
    status_code = 403

    def __init__(self, message: str = "Motoristas não podem adicionar dependentes.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class DependentNotFoundError(DomainError):
    code = "dependent_not_found"
    status_code = 404

    def __init__(self, message: str = "Dependente não encontrado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class DependentOwnershipError(DomainError):
    code = "dependent_ownership"
    status_code = 403

    def __init__(self, message: str = "Você não tem permissão para acessar este dependente.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
