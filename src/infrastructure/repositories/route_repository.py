from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.routes.entity import RouteModel
from src.domains.routes.repository import IRouteRepository


class RouteRepositoryImpl(IRouteRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, route: RouteModel) -> RouteModel:
        pass

    def find_by_id(self, route_id: UUID) -> RouteModel | None:
        pass

    def find_all_by_driver_id(self, driver_id: UUID) -> list[RouteModel]:
        pass

    def update_invite_code(self, route_id: UUID, new_code: str) -> RouteModel | None:
        pass
