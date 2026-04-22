"""US06 — DI do RoutePassangerService."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.dependents.repository import IDependentRepository
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.route_passangers.schedule_repository import (
    IRoutePassangerScheduleRepository,
)
from src.domains.route_passangers.service import RoutePassangerService
from src.domains.routes.repository import IRouteRepository
from src.domains.stops.repository import IStopRepository
from src.domains.users.repository import IUserRepository
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.dependent_dependencies import get_dependent_repository
from src.infrastructure.dependencies.notification_dependencies import get_notification_service
from src.infrastructure.dependencies.route_dependencies import get_route_repository
from src.infrastructure.dependencies.route_passanger_schedule_dependencies import (
    get_route_passanger_schedule_repository,
)
from src.infrastructure.dependencies.stop_dependencies import get_stop_repository
from src.infrastructure.dependencies.user_dependencies import get_user_repository
from src.infrastructure.repositories.route_passanger_repository import RoutePassangerRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_route_passanger_repository(db: DatabaseSession) -> IRoutePassangerRepository:
    return RoutePassangerRepositoryImpl(db)


def get_route_passanger_service(
    rp_repo: Annotated[IRoutePassangerRepository, Depends(get_route_passanger_repository)],
    route_repo: Annotated[IRouteRepository, Depends(get_route_repository)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    dependent_repo: Annotated[IDependentRepository, Depends(get_dependent_repository)],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
    stop_repo: Annotated[IStopRepository, Depends(get_stop_repository)],
    schedule_repo: Annotated[
        IRoutePassangerScheduleRepository,
        Depends(get_route_passanger_schedule_repository),
    ],
) -> RoutePassangerService:
    return RoutePassangerService(
        rp_repo,
        route_repo,
        user_repo,
        dependent_repo,
        notification_service,
        stop_repo,
        schedule_repo,
    )
