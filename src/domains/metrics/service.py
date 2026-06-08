"""US15 — MetricsService.

Traduz o período (day/week/month) em um intervalo de datas, consulta o
repositório de agregação e mapeia o resultado para `MetricsReportResponse`.
"""

import calendar
from datetime import date, datetime, time, timedelta
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
        if period == ReportPeriod.DAY:
            effective_start = start_date
            effective_end = start_date

        elif period == ReportPeriod.WEEK:
            effective_start = start_date
            effective_end = end_date if end_date is not None else start_date + timedelta(days=6)

        else:  # MONTH
            effective_start = start_date.replace(day=1)
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            effective_end = start_date.replace(day=last_day)

        start_dt = datetime.combine(effective_start, time(0, 0, 0))
        end_dt = datetime.combine(effective_end, time(23, 59, 59))

        agg = self.repository.aggregate_driver_metrics(driver_id, start=start_dt, end=end_dt)

        duration_minutes = round(agg.total_duration_seconds / 60)

        return MetricsReportResponse(
            distance=agg.total_km,
            duration=duration_minutes,
            passengers=agg.passengers,
            trips=agg.trips,
            period=period,
            start_date=effective_start,
            end_date=effective_end,
        )
