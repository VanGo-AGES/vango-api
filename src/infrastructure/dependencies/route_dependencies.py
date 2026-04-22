from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.routes.repository import IAddressRepository, IRouteRepository
from src.domains.routes.service import RouteService
from src.domains.vehicles.repository import IVehicleRepository
from src.infrastructure.database import get_db
from src.infrastructure.repositories.address_repository import AddressRepositoryImpl
from src.infrastructure.repositories.route_repository import RouteRepositoryImpl
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_address_repository(db: DatabaseSession) -> IAddressRepository:
    return AddressRepositoryImpl(db)


def get_route_repository(db: DatabaseSession) -> IRouteRepository:
    return RouteRepositoryImpl(db)


def get_vehicle_repository_for_routes(db: DatabaseSession) -> IVehicleRepository:
    return VehicleRepositoryImpl(db)


def get_route_service(
    route_repo: Annotated[IRouteRepository, Depends(get_route_repository)],
    address_repo: Annotated[IAddressRepository, Depends(get_address_repository)],
    vehicle_repo: Annotated[IVehicleRepository, Depends(get_vehicle_repository_for_routes)],
) -> RouteService:
    return RouteService(route_repo, address_repo, vehicle_repo)
