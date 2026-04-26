"""Erros do domínio route_passangers."""


class RoutePassangerNotFoundError(Exception):
    def __init__(self, message: str = "Solicitação ou vínculo de passageiro não encontrado") -> None:
        super().__init__(message)


class RouteCapacityExceededError(Exception):
    def __init__(self, message: str = "A rota atingiu o limite máximo de passageiros") -> None:
        super().__init__(message)


class RoutePassangerAlreadyProcessedError(Exception):
    def __init__(self, message: str = "A solicitação já foi aceita ou rejeitada anteriormente") -> None:
        super().__init__(message)


class DuplicateRoutePassangerError(Exception):
    """Passageiro já possui vínculo ativo (pending/accepted) com a rota."""

    pass


class NotRoutePassangerError(Exception):
    """Usuário não possui vínculo ativo (pending/accepted) com a rota,
    nem como passageiro, nem como guardian de um dependente."""

    def __init__(self, message: str = "Usuário não é passageiro desta rota") -> None:
        super().__init__(message)
