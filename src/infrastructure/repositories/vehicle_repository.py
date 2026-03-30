from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.repository import IVehicleRepository


# test
class VehicleRepositoryImpl(IVehicleRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, vehicle: VehicleModel) -> VehicleModel:
        pass

    def get_by_id(self, vehicle_id: UUID) -> VehicleModel | None:
        pass

    def get_by_driver_id(self, driver_id: UUID) -> list[VehicleModel]:
        pass

    def update(self, vehicle_id: UUID, data: dict) -> VehicleModel | None:
        pass

    def delete(self, vehicle_id: UUID) -> bool:
        pass
