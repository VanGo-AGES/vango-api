"""US08-TK02 — Implementação SQLAlchemy do IRoutePassangerScheduleRepository."""

from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel
from src.domains.route_passangers.schedule_repository import (
    IRoutePassangerScheduleRepository,
)


class RoutePassangerScheduleRepositoryImpl(IRoutePassangerScheduleRepository):
    def __init__(self, session: Session):
        self.session = session

    def save_many(self, schedules: list[RoutePassangerScheduleModel]) -> list[RoutePassangerScheduleModel]:
        pass

    def find_by_route_passanger_id(self, rp_id: UUID) -> list[RoutePassangerScheduleModel]:
        pass

    def delete_by_route_passanger_id(self, rp_id: UUID) -> int:
        pass

    def replace(
        self,
        rp_id: UUID,
        new_schedules: list[RoutePassangerScheduleModel],
    ) -> list[RoutePassangerScheduleModel]:
        pass
