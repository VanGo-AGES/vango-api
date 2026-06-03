"""US15-TK02 — Implementação do repositório de métricas (agregação SQL)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.metrics.repository import ITripMetricsRepository, MetricsAggregate


class TripMetricsRepositoryImpl(ITripMetricsRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US15-TK02
    def aggregate_driver_metrics(self, driver_id: UUID, start: datetime, end: datetime) -> MetricsAggregate:
        raise NotImplementedError("US15-TK02")
