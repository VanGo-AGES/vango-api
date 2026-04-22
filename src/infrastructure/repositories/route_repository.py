from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.routes.entity import RouteModel
from src.domains.routes.repository import IRouteRepository


class RouteRepositoryImpl(IRouteRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, route: RouteModel) -> RouteModel:
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def find_by_id(self, route_id: UUID) -> RouteModel | None:
        return self.session.query(RouteModel).filter(RouteModel.id == route_id).first()

    def find_all_by_driver_id(self, driver_id: UUID) -> list[RouteModel]:
        routes = self.session.query(RouteModel).filter(RouteModel.driver_id == driver_id).all()
        return routes

    def update_invite_code(self, route_id: UUID, new_code: str) -> RouteModel | None:
        route = self.session.query(RouteModel).filter(RouteModel.id == route_id).first()

        if route is None:
            return None

        route.invite_code = new_code
        self.session.commit()
        self.session.refresh(route)
        return route

    # US06-TK02
    def update(self, route_id: UUID, data: dict) -> RouteModel | None:
        pass

    # US08-TK05
    def find_by_invite_code(self, invite_code: str) -> RouteModel | None:
        pass

    # US06-TK17
    def delete(self, route_id: UUID) -> bool:
        pass
