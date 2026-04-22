"""US06-TK20 — DI do AbsenceService."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.absences.service import AbsenceService
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IRouteRepository
from src.domains.trips.repository import IAbsenceRepository
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.notification_dependencies import (
    get_notification_service,
)
from src.infrastructure.dependencies.route_dependencies import get_route_repository
from src.infrastructure.dependencies.route_passanger_dependencies import (
    get_route_passanger_repository,
)
from src.infrastructure.repositories.absence_repository import AbsenceRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_absence_repository(db: DatabaseSession) -> IAbsenceRepository:
    return AbsenceRepositoryImpl(db)


def get_absence_service(
    absence_repo: Annotated[IAbsenceRepository, Depends(get_absence_repository)],
    route_repo: Annotated[IRouteRepository, Depends(get_route_repository)],
    rp_repo: Annotated[IRoutePassangerRepository, Depends(get_route_passanger_repository)],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
) -> AbsenceService:
    return AbsenceService(
        absence_repo,
        route_repo,
        rp_repo,
        notification_service,
    )
