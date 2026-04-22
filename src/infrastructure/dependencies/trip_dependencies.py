"""US09 — DI do TripService e dos repositórios do domínio trips."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IRouteRepository
from src.domains.stops.repository import IStopRepository
from src.domains.trips.repository import (
    IAbsenceRepository,
    ITripPassangerRepository,
    ITripRepository,
)
from src.domains.trips.service import TripService
from src.domains.vehicles.repository import IVehicleRepository
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.notification_dependencies import get_notification_service
from src.infrastructure.dependencies.route_dependencies import get_route_repository
from src.infrastructure.dependencies.route_passanger_dependencies import (
    get_route_passanger_repository,
)
from src.infrastructure.dependencies.stop_dependencies import get_stop_repository
from src.infrastructure.dependencies.vehicle_dependencies import get_vehicle_repository
from src.infrastructure.repositories.absence_repository import AbsenceRepositoryImpl
from src.infrastructure.repositories.trip_passanger_repository import TripPassangerRepositoryImpl
from src.infrastructure.repositories.trip_repository import TripRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_trip_repository(db: DatabaseSession) -> ITripRepository:
    return TripRepositoryImpl(db)


def get_trip_passanger_repository(db: DatabaseSession) -> ITripPassangerRepository:
    return TripPassangerRepositoryImpl(db)


def get_absence_repository(db: DatabaseSession) -> IAbsenceRepository:
    return AbsenceRepositoryImpl(db)


def get_trip_service(
    trip_repo: Annotated[ITripRepository, Depends(get_trip_repository)],
    trip_passanger_repo: Annotated[ITripPassangerRepository, Depends(get_trip_passanger_repository)],
    absence_repo: Annotated[IAbsenceRepository, Depends(get_absence_repository)],
    route_repo: Annotated[IRouteRepository, Depends(get_route_repository)],
    rp_repo: Annotated[IRoutePassangerRepository, Depends(get_route_passanger_repository)],
    stop_repo: Annotated[IStopRepository, Depends(get_stop_repository)],
    vehicle_repo: Annotated[IVehicleRepository, Depends(get_vehicle_repository)],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
) -> TripService:
    return TripService(
        trip_repo,
        trip_passanger_repo,
        absence_repo,
        route_repo,
        rp_repo,
        stop_repo,
        vehicle_repo,
        notification_service,
    )
