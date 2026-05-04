class DuplicateEmailError(Exception):
    def __init__(self, message: str = "Este e-mail já está cadastrado."):
        super().__init__(message)


class UserNotFoundError(Exception):
    def __init__(self, message: str = "Usuário não encontrado."):
        super().__init__(message)


class InvalidCredentialsError(Exception):
    def __init__(self, message: str = "E-mail ou senha incorretos."):
        super().__init__(message)
