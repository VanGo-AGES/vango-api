"""US15 — DTOs de Métricas & Relatórios.

Contratos consumidos pela tela `trip-reports-screen` do app do motorista.
Os campos de `MetricsReportResponse` serão declarados na US15-TK01.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ReportPeriod(StrEnum):
    """Granularidade do relatório selecionada nas abas Dia / Semana / Mês."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# US15-TK01
class MetricsReportResponse(BaseModel):
    distance: float = 0.0
    duration: int = 0
    passengers: int = 0
    trips: int = 0
    period: ReportPeriod
    start_date: date
    end_date: date

    model_config = ConfigDict(from_attributes=True)
