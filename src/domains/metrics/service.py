"""US15 — MetricsService.

Traduz o período (day/week/month) em um intervalo de datas, consulta o
repositório de agregação e mapeia o resultado para `MetricsReportResponse`.
"""

from datetime import date
from uuid import UUID

from src.domains.metrics.dtos import MetricsReportResponse, ReportPeriod
from src.domains.metrics.repository import ITripMetricsRepository


class MetricsService:
    def __init__(self, repository: ITripMetricsRepository) -> None:
        self.repository = repository

    # US15-TK03
    def get_report(
        self,
        driver_id: UUID,
        period: ReportPeriod,
        start_date: date,
        end_date: date | None = None,
    ) -> MetricsReportResponse:
        """Monta o relatório agregado do motorista para o período pedido."""
        raise NotImplementedError("US15-TK03")
