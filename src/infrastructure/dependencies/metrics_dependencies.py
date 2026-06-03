"""US15 — Wiring de dependências de Métricas & Relatórios."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.metrics.repository import ITripMetricsRepository
from src.domains.metrics.service import MetricsService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.trip_metrics_repository import TripMetricsRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_trip_metrics_repository(db: DatabaseSession) -> ITripMetricsRepository:
    return TripMetricsRepositoryImpl(db)


def get_metrics_service(
    repo: Annotated[ITripMetricsRepository, Depends(get_trip_metrics_repository)],
) -> MetricsService:
    return MetricsService(repo)
