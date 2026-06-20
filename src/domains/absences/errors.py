"""Erros do domínio absences."""

from src.shared.errors import DomainError


class AbsenceAlreadyReportedError(DomainError):
    """Já existe ausência avisada para o mesmo RP naquela data."""

    code = "absence_already_reported"
    status_code = 409

    def __init__(self, message: str = "Ausência já registrada para esta data.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)


class AbsenceDateNotAllowedError(DomainError):
    """A data informada não é permitida (ex.: dia que já passou ou fora da
    recorrência da rota).
    """

    code = "absence_date_not_allowed"
    status_code = 409

    def __init__(self, message: str = "Data não permitida para registro de ausência.", details: dict | None = None) -> None:
        super().__init__(message=message, details=details)
