class VehicleAccessDeniedError(Exception):
    def __init__(self, message: str = "Apenas motoristas podem adicionar veículos."):
        super().__init__(message)


class VehicleNotFoundError(Exception):
    def __init__(self, message: str = "Veículo não encontrado."):
        super().__init__(message)


class VehicleOwnershipError(Exception):
    def __init__(self, message: str = "Você não tem permissão para acessar este veículo."):
        super().__init__(message)
