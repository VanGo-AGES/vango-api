"""Erros do domínio absences."""

from src.shared.errors import DomainError


class AbsenceAlreadyReportedError(DomainError):
    """Já existe ausência avisada para o mesmo RP naquela data."""

    code = "absence_already_reported"
    status_code = 409


class AbsenceDateNotAllowedError(DomainError):
    """A data informada não é permitida (ex.: dia que já passou ou fora da
    recorrência da rota).
    """

    code = "absence_date_not_allowed"
    status_code = 409
