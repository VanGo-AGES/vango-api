from src.shared.errors import DomainError


class VehiclePlateAlreadyExistsError(DomainError):
    code = "vehicle_plate_already_exists"
    status_code = 409

    def __init__(self, message: str = "Já existe um veículo com esta placa.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class VehicleAccessDeniedError(DomainError):
    code = "vehicle_access_denied"
    status_code = 403

    def __init__(self, message: str = "Apenas motoristas podem adicionar veículos.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class VehicleNotFoundError(DomainError):
    code = "vehicle_not_found"
    status_code = 404

    def __init__(self, message: str = "Veículo não encontrado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class VehicleOwnershipError(DomainError):
    code = "vehicle_ownership"
    status_code = 403

    def __init__(self, message: str = "Você não tem permissão para acessar este veículo.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
