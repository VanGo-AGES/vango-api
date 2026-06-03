"""US15 — DTOs de Métricas & Relatórios.

Contratos consumidos pela tela `trip-reports-screen` do app do motorista.
Os campos de `MetricsReportResponse` serão declarados na US15-TK01.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ReportPeriod(StrEnum):
    """Granularidade do relatório selecionada nas abas Dia / Semana / Mês."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# US15-TK01
class MetricsReportResponse(BaseModel):
    """Resposta agregada do relatório de viagens do motorista.

    Campos esperados (implementar na US15-TK01):
    - distance: float        — km rodados no período
    - duration: int          — tempo total das viagens, em minutos
    - passengers: int        — passageiros transportados
    - trips: int             — viagens realizadas
    - period: ReportPeriod   — granularidade aplicada
    - start_date: date       — início do intervalo considerado
    - end_date: date         — fim do intervalo considerado
    """

    model_config = ConfigDict(from_attributes=True)

    # TODO US15-TK01: declarar os campos acima (com defaults zerados onde fizer sentido).
