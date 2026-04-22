"""Erros do domínio route_passangers."""


class RoutePassangerNotFoundError(Exception):
    pass


class RouteCapacityExceededError(Exception):
    pass


class RoutePassangerAlreadyProcessedError(Exception):
    pass


class DuplicateRoutePassangerError(Exception):
    """Passageiro já possui vínculo ativo (pending/accepted) com a rota."""

    pass


class NotRoutePassangerError(Exception):
    """Usuário não possui vínculo ativo (pending/accepted) com a rota,
    nem como passageiro, nem como guardian de um dependente."""

    def __init__(self, message: str = "Usuário não é passageiro desta rota") -> None:
        super().__init__(message)
