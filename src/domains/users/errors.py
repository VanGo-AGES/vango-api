from src.shared.errors import DomainError


class DuplicateEmailError(DomainError):
    code = "duplicate_email"
    status_code = 400

    def __init__(self, message: str = "Este e-mail já está cadastrado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class UserNotFoundError(DomainError):
    code = "user_not_found"
    status_code = 404

    def __init__(self, message: str = "Usuário não encontrado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class InvalidCredentialsError(DomainError):
    code = "invalid_credentials"
    status_code = 401

    def __init__(self, message: str = "E-mail ou senha incorretos.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
