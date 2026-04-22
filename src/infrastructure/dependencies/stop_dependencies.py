"""US07-TK08 — DI do IStopRepository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.stops.repository import IStopRepository
from src.infrastructure.database import get_db
from src.infrastructure.repositories.stop_repository import StopRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_stop_repository(db: DatabaseSession) -> IStopRepository:
    return StopRepositoryImpl(db)
