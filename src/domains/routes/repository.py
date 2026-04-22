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

    # US06-TK02
    @abstractmethod
    def update(self, route_id: UUID, data: dict) -> RouteModel | None:
        pass

    # US08-TK05
    @abstractmethod
    def find_by_invite_code(self, invite_code: str) -> RouteModel | None:
        """Localiza rota pelo invite_code. Retorna None se não existir."""
        pass

    # US06-TK17
    @abstractmethod
    def delete(self, route_id: UUID) -> bool:
        """Remove fisicamente a rota pelo id.

        Retorna True se removeu, False se não existia.
        A cascata do ORM (cascade="all, delete-orphan") cuida de
        route_passangers, schedules e stops associadas.
        """
        pass
