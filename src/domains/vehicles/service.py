import uuid

from src.domains.vehicles.dtos import VehicleCreate, VehicleUpdate
from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.errors import VehicleAccessDeniedError, VehicleNotFoundError, VehicleOwnershipError
from src.domains.vehicles.repository import IVehicleRepository


class VehicleService:
    def __init__(self, repository: IVehicleRepository):
        self.repository = repository

    def add_vehicle(self, user_id: str, user_role: str, data: VehicleCreate) -> VehicleModel:
        if user_role != "driver":
            raise VehicleAccessDeniedError()
        vehicle = VehicleModel(
            driver_id=uuid.UUID(user_id),
            plate=data.plate,
            capacity=data.capacity,
            notes=data.notes,
        )
        return self.repository.create(vehicle)

    def get_vehicles(self, user_id: str) -> list[VehicleModel]:
        return self.repository.get_by_driver_id(uuid.UUID(user_id))

    def get_vehicle(self, user_id: str, vehicle_id: uuid.UUID) -> VehicleModel:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        return vehicle

    def update_vehicle(self, user_id: str, vehicle_id: uuid.UUID, data: VehicleUpdate) -> VehicleModel:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        return self.repository.update(vehicle_id, data.model_dump(exclude_none=True))

    def delete_vehicle(self, user_id: str, vehicle_id: uuid.UUID) -> None:
        vehicle = self.repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        if str(vehicle.driver_id) != user_id:
            raise VehicleOwnershipError()
        self.repository.delete(vehicle_id)
