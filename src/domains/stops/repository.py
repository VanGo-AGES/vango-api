"""US07-TK07 — Interface do repositório de stops."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.stops.entity import StopModel


class IStopRepository(ABC):
    @abstractmethod
    def save(self, stop: StopModel) -> StopModel:
        pass

    @abstractmethod
    def find_by_id(self, stop_id: UUID) -> StopModel | None:
        pass

    @abstractmethod
    def find_by_route_id(self, route_id: UUID) -> list[StopModel]:
        pass

    @abstractmethod
    def find_by_route_passanger_id(self, rp_id: UUID) -> StopModel | None:
        pass

    @abstractmethod
    def delete_by_route_passanger_id(self, rp_id: UUID) -> bool:
        pass
