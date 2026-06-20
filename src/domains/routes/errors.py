from src.shared.errors import DomainError


class RouteNotFoundError(DomainError):
    code = "route_not_found"
    status_code = 404

    def __init__(self, message: str = "Rota não encontrada.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class RouteOwnershipError(DomainError):
    code = "route_ownership"
    status_code = 403

    def __init__(self, message: str = "Você não tem permissão para acessar esta rota.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class NoVehicleError(DomainError):
    code = "no_vehicle"
    status_code = 400

    def __init__(self, message: str = "O motorista não possui veículo cadastrado.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class DuplicateInviteCodeError(DomainError):
    code = "duplicate_invite_code"
    status_code = 409

    def __init__(self, message: str = "Erro ao gerar código de convite único. Tente novamente.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


# US06
class RouteInProgressError(DomainError):
    code = "route_in_progress"
    status_code = 409

    def __init__(self, message: str = "Não é possível modificar uma rota em andamento.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
