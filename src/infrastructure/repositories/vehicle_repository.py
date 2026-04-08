from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.repository import IVehicleRepository


class VehicleRepositoryImpl(IVehicleRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, vehicle: VehicleModel) -> VehicleModel:
        self.session.add(vehicle)
        self.session.commit()
        self.session.refresh(vehicle)
        return vehicle

    def get_by_id(self, vehicle_id: UUID) -> VehicleModel | None:
        return self.session.query(VehicleModel).filter(VehicleModel.id == vehicle_id).first()

    def get_by_driver_id(self, driver_id: UUID) -> list[VehicleModel]:
        return self.session.query(VehicleModel).filter(VehicleModel.driver_id == driver_id).all()

    def update(self, vehicle_id: UUID, data: dict) -> VehicleModel | None:
        vehicle = self.get_by_id(vehicle_id)
        if vehicle is None:
            return None

        for key, value in data.items():
            setattr(vehicle, key, value)

        self.session.commit()
        self.session.refresh(vehicle)
        return vehicle

    def delete(self, vehicle_id: UUID) -> bool:
        vehicle = self.get_by_id(vehicle_id)
        if vehicle is None:
            return False

        self.session.delete(vehicle)
        self.session.commit()
        return True
