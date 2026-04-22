from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.addresses.entity import AddressModel
from src.domains.routes.entity import RouteModel


class IAddressRepository(ABC):
    @abstractmethod
    def save(self, address: AddressModel) -> AddressModel:
        pass


class IRouteRepository(ABC):
    @abstractmethod
    def save(self, route: RouteModel) -> RouteModel:
        pass

    @abstractmethod
    def find_by_id(self, route_id: UUID) -> RouteModel | None:
        pass

    @abstractmethod
    def find_all_by_driver_id(self, driver_id: UUID) -> list[RouteModel]:
        pass

    @abstractmethod
    def update_invite_code(self, route_id: UUID, new_code: str) -> RouteModel | None:
        pass
