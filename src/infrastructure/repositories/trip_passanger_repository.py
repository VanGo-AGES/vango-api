"""US09 — Implementação SQLAlchemy do ITripPassangerRepository.

TK03 cobre: save_all, find_by_id, find_by_trip, update_status, bulk_alight_presents.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.stops.entity import StopModel
from src.domains.trips.entity import TripPassangerModel
from src.domains.trips.repository import ITripPassangerRepository


class TripPassangerRepositoryImpl(ITripPassangerRepository):
    def __init__(self, session: Session):
        self.session = session

    # US09-TK03
    def save_all(self, trip_passangers: list[TripPassangerModel]) -> list[TripPassangerModel]:
        for tp in trip_passangers:
            self.session.add(tp)
        self.session.flush()
        return trip_passangers

    # US09-TK03
    def find_by_id(self, trip_passanger_id: UUID) -> TripPassangerModel | None:
        return self.session.get(TripPassangerModel, trip_passanger_id)

    # US09-TK03
    def find_by_trip(self, trip_id: UUID) -> list[TripPassangerModel]:
        stmt = (
            select(TripPassangerModel)
            .join(RoutePassangerModel, TripPassangerModel.route_passanger_id == RoutePassangerModel.id)
            .outerjoin(StopModel, StopModel.route_passanger_id == RoutePassangerModel.id)
            .where(TripPassangerModel.trip_id == trip_id)
            .order_by(StopModel.order_index.nulls_last())
        )
        return list(self.session.execute(stmt).scalars().all())

    # US09-TK03
    def update_status(
        self,
        trip_passanger_id: UUID,
        status: str,
        boarded_at: datetime | None = None,
        alighted_at: datetime | None = None,
    ) -> TripPassangerModel | None:
        tp = self.find_by_id(trip_passanger_id)
        if tp is None:
            return None
        tp.status = status
        if boarded_at is not None:
            tp.boarded_at = boarded_at
        if alighted_at is not None:
            tp.alighted_at = alighted_at
        self.session.flush()
        return tp

    # US09-TK03
    def bulk_alight_presents(self, trip_id: UUID, alighted_at: datetime) -> int:
        stmt = (
            update(TripPassangerModel)
            .where(
                TripPassangerModel.trip_id == trip_id,
                TripPassangerModel.status == "presente",
                TripPassangerModel.alighted_at.is_(None),
            )
            .values(alighted_at=alighted_at)
            .execution_options(synchronize_session="fetch")
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount
