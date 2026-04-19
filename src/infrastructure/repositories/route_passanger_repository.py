"""US06-TK06 — Implementação do repositório de route_passangers."""

from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.route_passangers.repository import IRoutePassangerRepository


class RoutePassangerRepositoryImpl(IRoutePassangerRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, rp_id: UUID) -> RoutePassangerModel | None:
        pass

    def find_by_route_and_status(self, route_id: UUID, status: str | None = None) -> list[RoutePassangerModel]:
        pass

    def update_status(self, rp_id: UUID, new_status: str) -> RoutePassangerModel | None:
        pass

    def count_accepted_by_route(self, route_id: UUID) -> int:
        pass

    def delete(self, rp_id: UUID) -> bool:
        pass
