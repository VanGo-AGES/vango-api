class DuplicateEmailError(Exception):
    def __init__(self, message: str = "Este e-mail já está cadastrado."):
        super().__init__(message)
