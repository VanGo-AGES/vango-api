"""US09 — Exceções de domínio para execução de viagem."""

from src.shared.errors import DomainError


class TripError(DomainError):
    """Base para erros do domínio trips."""

    code = "trip_error"
    status_code = 400


class TripNotFoundError(TripError):
    """Trip não existe."""

    code = "trip_not_found"
    status_code = 404


class TripOwnershipError(TripError):
    """O motorista que fez a requisição não é dono da rota/trip."""

    code = "trip_ownership"
    status_code = 403


class TripAlreadyInProgressError(TripError):
    """Já existe uma trip iniciada para a rota — não pode iniciar outra."""

    code = "trip_already_in_progress"
    status_code = 409


class TripNotInProgressError(TripError):
    """A trip não está no status 'iniciada' — ação inválida (ex: marcar
    embarque após finalizar).
    """

    code = "trip_not_in_progress"
    status_code = 409


class TripAlreadyFinishedError(TripError):
    """A trip já foi finalizada."""

    code = "trip_already_finished"
    status_code = 409


class VehicleNotOwnedError(TripError):
    """O vehicle informado não pertence ao motorista."""

    code = "vehicle_not_owned"
    status_code = 403


class TripPassangerNotFoundError(TripError):
    """trip_passanger não encontrado."""

    code = "trip_passanger_not_found"
    status_code = 404


class TripStopNotFoundError(TripError):
    """Stop não pertence à trip (rota da trip)."""

    code = "trip_stop_not_found"
    status_code = 404


class InvalidTripPassangerStatusError(TripError):
    """Transição de status inválida (ex: marcar como embarcado alguém já
    marcado como ausente).
    """

    code = "invalid_trip_passanger_status"
    status_code = 409


class NoPassangersToStartError(TripError):
    """A rota não tem passageiros aceitos — iniciar viagem não faz sentido."""

    code = "no_passangers_to_start"
    status_code = 409
