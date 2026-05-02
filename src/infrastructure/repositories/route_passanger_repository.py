"""US06-TK06 — Implementação do repositório de route_passangers."""

from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.domains.dependents.entity import DependentModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.entity import RouteModel


class RoutePassangerRepositoryImpl(IRoutePassangerRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, rp: RoutePassangerModel) -> RoutePassangerModel:
        self.session.add(rp)
        self.session.flush()
        self.session.refresh(rp)
        return rp

    def find_by_id(self, rp_id: UUID) -> RoutePassangerModel | None:
        return self.session.query(RoutePassangerModel).filter(RoutePassangerModel.id == rp_id).first()

    def find_by_route_and_status(self, route_id: UUID, status: str | None = None) -> list[RoutePassangerModel]:
        query = self.session.query(RoutePassangerModel).filter(RoutePassangerModel.route_id == route_id)
        if status is not None:
            query = query.filter(RoutePassangerModel.status == status)
        return query.all()

    def update_status(self, rp_id: UUID, new_status: str) -> RoutePassangerModel | None:
        rp = self.session.query(RoutePassangerModel).filter(RoutePassangerModel.id == rp_id).first()
        if rp:
            rp.status = new_status
            self.session.commit()
            return rp
        return None

    def count_accepted_by_route(self, route_id: UUID) -> int:
        return (
            self.session.query(RoutePassangerModel)
            .filter(RoutePassangerModel.route_id == route_id, RoutePassangerModel.status == "accepted")
            .count()
        )

    def delete(self, rp_id: UUID) -> bool:
        rp = self.session.query(RoutePassangerModel).filter(RoutePassangerModel.id == rp_id).first()
        if rp:
            self.session.delete(rp)
            self.session.commit()
            return True
        return False

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
        return (
            self.session.query(RoutePassangerModel)
            .options(
                joinedload(RoutePassangerModel.route).joinedload(RouteModel.driver),
                joinedload(RoutePassangerModel.route).joinedload(RouteModel.origin_address),
                joinedload(RoutePassangerModel.route).joinedload(RouteModel.destination_address),
                joinedload(RoutePassangerModel.schedules),
            )
            .outerjoin(RoutePassangerModel.dependent)
            .filter(
                RoutePassangerModel.status.in_(["pending", "accepted"]),
                or_(RoutePassangerModel.user_id == user_id, DependentModel.guardian_id == user_id),
            )
            .order_by(RoutePassangerModel.joined_at.desc())
            .all()
        )
