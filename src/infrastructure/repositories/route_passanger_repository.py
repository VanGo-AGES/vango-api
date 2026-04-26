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

    # -------------------------------------------------------------------
    # US08-TK03
    # -------------------------------------------------------------------

    def find_active_by_user_and_route(
        self,
        user_id: UUID,
        dependent_id: UUID | None,
        route_id: UUID,
    ) -> RoutePassangerModel | None:
        dependent_filter = (
            RoutePassangerModel.dependent_id == dependent_id if dependent_id is not None else RoutePassangerModel.dependent_id.is_(None)
        )
        return (
            self.session.query(RoutePassangerModel)
            .filter(
                RoutePassangerModel.user_id == user_id,
                dependent_filter,
                RoutePassangerModel.route_id == route_id,
                RoutePassangerModel.status.in_(["pending", "accepted"]),
            )
            .first()
        )

    def find_by_user_and_route_id(
        self,
        user_id: UUID,
        route_id: UUID,
    ) -> list[RoutePassangerModel]:
        return (
            self.session.query(RoutePassangerModel)
            .filter(
                RoutePassangerModel.user_id == user_id,
                RoutePassangerModel.route_id == route_id,
            )
            .all()
        )

    # -------------------------------------------------------------------
    # US08-TK13
    # -------------------------------------------------------------------

    def find_active_with_route_by_user(
        self,
        user_id: UUID,
    ) -> list[RoutePassangerModel]:
        pass
