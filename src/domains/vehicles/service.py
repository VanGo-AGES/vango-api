from src.domains.vehicles.dtos import VehicleCreate, VehicleUpdate
from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.errors import VehicleNotFoundError, VehicleOwnershipError
from src.domains.vehicles.repository import IVehicleRepository


class VehicleService:
    def __init__(self, repository: IVehicleRepository):
        self.repository = repository

    def add_vehicle(self, user_id: str, user_role: str, data: VehicleCreate) -> VehicleModel:
        pass

    def get_vehicles(self, user_id: str) -> list[VehicleModel]:
        return self.repository.get_by_driver_id(user_id)

    def get_vehicle(self, user_id: str, vehicle_id: str) -> VehicleModel:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        return vehicle

    def update_vehicle(self, user_id: str, vehicle_id: str, data: VehicleUpdate) -> VehicleModel:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        return self.repository.update(vehicle_id, data.model_dump(exclude_none=True))

    def delete_vehicle(self, user_id: str, vehicle_id: str) -> None:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        self.repository.delete(vehicle_id)
