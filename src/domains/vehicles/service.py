from src.domains.vehicles.dtos import VehicleCreate, VehicleUpdate
from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.repository import IVehicleRepository


class VehicleService:
    def __init__(self, repository: IVehicleRepository):
        self.repository = repository

    def add_vehicle(self, user_id: str, user_role: str, data: VehicleCreate) -> VehicleModel:
        pass

    def get_vehicles(self, user_id: str) -> list[VehicleModel]:
        pass

    def get_vehicle(self, user_id: str, vehicle_id: str) -> VehicleModel:
        pass

    def update_vehicle(self, user_id: str, vehicle_id: str, data: VehicleUpdate) -> VehicleModel:
        pass

    def delete_vehicle(self, user_id: str, vehicle_id: str) -> None:
        pass
