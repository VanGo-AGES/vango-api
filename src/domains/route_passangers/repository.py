"""US06-TK06 — Interface do repositório de route_passangers."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.route_passangers.entity import RoutePassangerModel


class IRoutePassangerRepository(ABC):
    @abstractmethod
    def find_by_id(self, rp_id: UUID) -> RoutePassangerModel | None:
        pass

    @abstractmethod
    def find_by_route_and_status(self, route_id: UUID, status: str | None = None) -> list[RoutePassangerModel]:
        pass

    @abstractmethod
    def update_status(self, rp_id: UUID, new_status: str) -> RoutePassangerModel | None:
        pass

    @abstractmethod
    def count_accepted_by_route(self, route_id: UUID) -> int:
        pass

    @abstractmethod
    def delete(self, rp_id: UUID) -> bool:
        pass
