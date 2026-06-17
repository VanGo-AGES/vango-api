"""Erros do domínio route_passangers."""

from src.shared.errors import DomainError


class RoutePassangerNotFoundError(DomainError):
    code = "route_passanger_not_found"
    status_code = 404

    def __init__(self, message: str = "Solicitação ou vínculo de passageiro não encontrado", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class RouteCapacityExceededError(DomainError):
    code = "route_capacity_exceeded"
    status_code = 409

    def __init__(self, message: str = "A rota atingiu o limite máximo de passageiros", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class RoutePassangerAlreadyProcessedError(DomainError):
    code = "route_passanger_already_processed"
    status_code = 409

    def __init__(self, message: str = "A solicitação já foi aceita ou rejeitada anteriormente", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class DuplicateRoutePassangerError(DomainError):
    """Passageiro já possui vínculo ativo (pending/accepted) com a rota."""

    code = "duplicate_route_passanger"
    status_code = 409


class NotRoutePassangerError(DomainError):
    """Usuário não possui vínculo ativo (pending/accepted) com a rota,
    nem como passageiro, nem como guardian de um dependente."""

    code = "not_route_passanger"
    status_code = 403

    def __init__(self, message: str = "Usuário não é passageiro desta rota", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
