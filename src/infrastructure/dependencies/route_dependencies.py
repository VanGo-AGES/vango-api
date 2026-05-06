from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IAddressRepository, IRouteRepository
from src.domains.routes.service import RouteService
from src.domains.trips.repository import IAbsenceRepository
from src.domains.vehicles.repository import IVehicleRepository
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.notification_dependencies import get_notification_service
from src.infrastructure.repositories.absence_repository import AbsenceRepositoryImpl
from src.infrastructure.repositories.address_repository import AddressRepositoryImpl
from src.infrastructure.repositories.route_passanger_repository import (
    RoutePassangerRepositoryImpl,
)
from src.infrastructure.repositories.route_repository import RouteRepositoryImpl
from src.infrastructure.repositories.vehicle_repository import VehicleRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_address_repository(db: DatabaseSession) -> IAddressRepository:
    return AddressRepositoryImpl(db)


def get_route_repository(db: DatabaseSession) -> IRouteRepository:
    return RouteRepositoryImpl(db)


def get_vehicle_repository_for_routes(db: DatabaseSession) -> IVehicleRepository:
    return VehicleRepositoryImpl(db)


# US08-TK05: usado por RouteService.get_invite_summary.
# Definido aqui (em vez de importar de route_passanger_dependencies) para
# evitar import circular entre os dois módulos de dependências.
def get_route_passanger_repository_for_routes(
    db: DatabaseSession,
) -> IRoutePassangerRepository:
    return RoutePassangerRepositoryImpl(db)


def get_absence_repository_for_routes(db: DatabaseSession) -> IAbsenceRepository:
    return AbsenceRepositoryImpl(db)


def get_route_service(
    route_repo: Annotated[IRouteRepository, Depends(get_route_repository)],
    address_repo: Annotated[IAddressRepository, Depends(get_address_repository)],
    vehicle_repo: Annotated[IVehicleRepository, Depends(get_vehicle_repository_for_routes)],
    rp_repo: Annotated[
        IRoutePassangerRepository,
        Depends(get_route_passanger_repository_for_routes),
    ],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
    absence_repo: Annotated[IAbsenceRepository, Depends(get_absence_repository_for_routes)],
) -> RouteService:
    return RouteService(route_repo, address_repo, vehicle_repo, rp_repo, notification_service, absence_repo)
