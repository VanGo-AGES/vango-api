"""US09 — Exceções de domínio para execução de viagem."""


class TripError(Exception):
    """Base para erros do domínio trips."""


class TripNotFoundError(TripError):
    """Trip não existe."""


class TripOwnershipError(TripError):
    """O motorista que fez a requisição não é dono da rota/trip."""


class TripAlreadyInProgressError(TripError):
    """Já existe uma trip iniciada para a rota — não pode iniciar outra."""


class TripNotInProgressError(TripError):
    """A trip não está no status 'iniciada' — ação inválida (ex: marcar
    embarque após finalizar).
    """


class TripAlreadyFinishedError(TripError):
    """A trip já foi finalizada."""


class VehicleNotOwnedError(TripError):
    """O vehicle informado não pertence ao motorista."""


class TripPassangerNotFoundError(TripError):
    """trip_passanger não encontrado."""


class TripStopNotFoundError(TripError):
    """Stop não pertence à trip (rota da trip)."""


class InvalidTripPassangerStatusError(TripError):
    """Transição de status inválida (ex: marcar como embarcado alguém já
    marcado como ausente).
    """


class NoPassangersToStartError(TripError):
    """A rota não tem passageiros aceitos — iniciar viagem não faz sentido."""
