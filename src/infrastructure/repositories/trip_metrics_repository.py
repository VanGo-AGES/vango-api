"""US15-TK02 — Implementação do repositório de métricas (agregação SQL)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from src.domains.metrics.repository import ITripMetricsRepository, MetricsAggregate
from src.domains.routes.entity import RouteModel
from src.domains.trips.entity import TripModel, TripPassangerModel


class TripMetricsRepositoryImpl(ITripMetricsRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # US15-TK02
    def aggregate_driver_metrics(self, driver_id: UUID, start: datetime, end: datetime) -> MetricsAggregate:
        dialect = self.session.get_bind().dialect.name

        if dialect == "sqlite":
            duration_expr = cast(
                (func.julianday(TripModel.finished_at) - func.julianday(TripModel.started_at)) * 86400,
                Integer,
            )
        else:
            duration_expr = cast(
                func.extract("epoch", TripModel.finished_at - TripModel.started_at),
                Integer,
            )

        # Correlated subquery avoids fan-out from the one-to-many join with trip_passangers
        passengers_per_trip = (
            select(func.count(TripPassangerModel.id))
            .where(
                TripPassangerModel.trip_id == TripModel.id,
                TripPassangerModel.status == "presente",
            )
            .correlate(TripModel)
            .scalar_subquery()
        )

        row = (
            self.session.query(
                func.coalesce(func.sum(TripModel.total_km), 0.0).label("total_km"),
                func.coalesce(func.sum(duration_expr), 0).label("total_duration_seconds"),
                func.coalesce(func.sum(passengers_per_trip), 0).label("passengers"),
                func.count(TripModel.id).label("trips"),
            )
            .join(RouteModel, RouteModel.id == TripModel.route_id)
            .filter(
                RouteModel.driver_id == driver_id,
                TripModel.status == "finalizada",
                TripModel.trip_date >= start,
                TripModel.trip_date <= end,
            )
            .one()
        )

        return MetricsAggregate(
            total_km=float(row.total_km),
            total_duration_seconds=int(row.total_duration_seconds),
            passengers=int(row.passengers),
            trips=int(row.trips),
        )
