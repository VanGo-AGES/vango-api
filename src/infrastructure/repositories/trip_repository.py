"""US09 — Implementação SQLAlchemy do ITripRepository.

Todos os métodos começam com pass (stub). As TKs correspondentes cobrem:
- TK02: save, find_by_id, find_in_progress_by_route, update_status
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.trips.entity import TripModel
from src.domains.trips.repository import ITripRepository


class TripRepositoryImpl(ITripRepository):
    def __init__(self, session: Session):
        self.session = session

    # US09-TK02
    def save(self, trip: TripModel) -> TripModel:
        pass

    # US09-TK02
    def find_by_id(self, trip_id: UUID) -> TripModel | None:
        pass

    # US09-TK02
    def find_in_progress_by_route(self, route_id: UUID) -> TripModel | None:
        pass

    # US09-TK02
    def update_status(
        self,
        trip_id: UUID,
        status: str,
        finished_at: datetime | None,
        total_km: float | None,
    ) -> TripModel | None:
        pass
