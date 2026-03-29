class RouteNotFoundError(Exception):
    def __init__(self, message: str = "Rota não encontrada."):
        super().__init__(message)


class RouteOwnershipError(Exception):
    def __init__(self, message: str = "Você não tem permissão para acessar esta rota."):
        super().__init__(message)


class NoVehicleError(Exception):
    def __init__(self, message: str = "O motorista não possui veículo cadastrado."):
        super().__init__(message)


class DuplicateInviteCodeError(Exception):
    def __init__(self, message: str = "Erro ao gerar código de convite único. Tente novamente."):
        super().__init__(message)
