class DependentAccessDeniedError(Exception):
    def __init__(self, message: str = "Motoristas não podem adicionar dependentes."):
        super().__init__(message)


class DependentNotFoundError(Exception):
    def __init__(self, message: str = "Dependente não encontrado."):
        super().__init__(message)


class DependentOwnershipError(Exception):
    def __init__(self, message: str = "Você não tem permissão para acessar este dependente."):
        super().__init__(message)
