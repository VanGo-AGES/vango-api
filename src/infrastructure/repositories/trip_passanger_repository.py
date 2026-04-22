"""US09 — Implementação SQLAlchemy do ITripPassangerRepository.

TK03 cobre: save_all, find_by_id, find_by_trip, update_status, bulk_alight_presents.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.trips.entity import TripPassangerModel
from src.domains.trips.repository import ITripPassangerRepository


class TripPassangerRepositoryImpl(ITripPassangerRepository):
    def __init__(self, session: Session):
        self.session = session

    # US09-TK03
    def save_all(self, trip_passangers: list[TripPassangerModel]) -> list[TripPassangerModel]:
        pass

    # US09-TK03
    def find_by_id(self, trip_passanger_id: UUID) -> TripPassangerModel | None:
        pass

    # US09-TK03
    def find_by_trip(self, trip_id: UUID) -> list[TripPassangerModel]:
        pass

    # US09-TK03
    def update_status(
        self,
        trip_passanger_id: UUID,
        status: str,
        boarded_at: datetime | None = None,
        alighted_at: datetime | None = None,
    ) -> TripPassangerModel | None:
        pass

    # US09-TK03
    def bulk_alight_presents(self, trip_id: UUID, alighted_at: datetime) -> int:
        pass
