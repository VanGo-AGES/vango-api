"""US08-TK02 — DI do IRoutePassangerScheduleRepository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.route_passangers.schedule_repository import (
    IRoutePassangerScheduleRepository,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.route_passanger_schedule_repository import (
    RoutePassangerScheduleRepositoryImpl,
)

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_route_passanger_schedule_repository(
    db: DatabaseSession,
) -> IRoutePassangerScheduleRepository:
    return RoutePassangerScheduleRepositoryImpl(db)
