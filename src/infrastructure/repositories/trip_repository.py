"""US09 — Implementação SQLAlchemy do ITripRepository.

Todos os métodos começam com pass (stub). As TKs correspondentes cobrem:
- TK02: save, find_by_id, find_in_progress_by_route, update_status
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.domains.trips.entity import TripModel
from src.domains.trips.repository import ITripRepository


class TripRepositoryImpl(ITripRepository):
    def __init__(self, session: Session):
        self.session = session

    # US09-TK02
    def save(self, trip: TripModel) -> TripModel:
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip

    # US09-TK02
    def find_by_id(self, trip_id: UUID) -> TripModel | None:
        stmt = (
            select(TripModel)
            .options(
                joinedload(TripModel.route),
                joinedload(TripModel.vehicle),
                joinedload(TripModel.trip_passangers),
                joinedload(TripModel.absences),
            )
            .where(TripModel.id == trip_id)
        )

        return self.session.execute(stmt).unique().scalar_one_or_none()

    # US09-TK02
    def find_in_progress_by_route(self, route_id: UUID) -> TripModel | None:
        stmt = (
            select(TripModel)
            .options(
                joinedload(TripModel.route),
                joinedload(TripModel.vehicle),
                joinedload(TripModel.trip_passangers),
                joinedload(TripModel.absences),
            )
            .where(
                TripModel.route_id == route_id,
                TripModel.status == "iniciada",
            )
        )

        return self.session.execute(stmt).unique().scalar_one_or_none()

    # US09-TK02
    def update_status(
        self,
        trip_id: UUID,
        status: str,
        finished_at: datetime | None,
        total_km: float | None,
    ) -> TripModel | None:
        trip = self.find_by_id(trip_id)

        if trip is None:
            return None

        trip.status = status
        trip.finished_at = finished_at
        trip.total_km = total_km

        self.session.commit()

        self.session.refresh(trip)

        return trip
