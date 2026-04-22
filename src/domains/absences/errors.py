"""Erros do domínio absences."""


class AbsenceAlreadyReportedError(Exception):
    """Já existe ausência avisada para o mesmo RP naquela data."""

    pass


class AbsenceDateNotAllowedError(Exception):
    """A data informada não é permitida (ex.: dia que já passou ou fora da
    recorrência da rota).
    """

    pass
