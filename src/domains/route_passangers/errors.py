"""US06-TK05 — Erros do domínio route_passangers.

Stubs das exceções de negócio. O desenvolvedor deve implementar as mensagens
default (em pt-BR) e garantir que herdem de Exception.
"""


class RoutePassangerNotFoundError(Exception):
    pass


class RouteCapacityExceededError(Exception):
    pass


class RoutePassangerAlreadyProcessedError(Exception):
    pass
