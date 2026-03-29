from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.vehicles.repository import IVehicleRepository
from src.domains.vehicles.service import VehicleService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_vehicle_repository(db: DatabaseSession) -> IVehicleRepository:
    return VehicleRepositoryImpl(db)


def get_vehicle_service(
    repo: Annotated[IVehicleRepository, Depends(get_vehicle_repository)],
) -> VehicleService:
    return VehicleService(repo)
