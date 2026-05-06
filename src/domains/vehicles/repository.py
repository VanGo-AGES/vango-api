from abc import ABC, abstractmethod
from uuid import UUID

from .entity import VehicleModel


class IVehicleRepository(ABC):
    @abstractmethod
    def create(self, vehicle: VehicleModel) -> VehicleModel:
        pass

    @abstractmethod
    def get_by_id(self, vehicle_id: UUID) -> VehicleModel | None:
        pass

    @abstractmethod
    def get_by_plate(self, plate: str) -> VehicleModel | None:
        pass

    @abstractmethod
    def get_by_driver_id(self, driver_id: UUID) -> list[VehicleModel]:
        pass

    @abstractmethod
    def update(self, vehicle_id: UUID, data: dict) -> VehicleModel | None:
        pass

    @abstractmethod
    def delete(self, vehicle_id: UUID) -> bool:
        pass

    @abstractmethod
    def find_by_id(self, vehicle_id: UUID) -> VehicleModel | None:
        pass
