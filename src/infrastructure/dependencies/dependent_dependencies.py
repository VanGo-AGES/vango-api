from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.dependents.repository import IDependentRepository
from src.domains.dependents.service import DependentService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.dependent_repository import DependentRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_dependent_repository(db: DatabaseSession) -> IDependentRepository:
    return DependentRepositoryImpl(db)


def get_dependent_service(
    repo: Annotated[IDependentRepository, Depends(get_dependent_repository)],
) -> DependentService:
    return DependentService(repo)
