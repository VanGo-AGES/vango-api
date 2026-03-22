from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories.user_repository import UserRepositoryImpl

from .repository import IUserRepository
from .service import UserService

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DatabaseSession) -> IUserRepository:
    return UserRepositoryImpl(db)


def get_user_service(repo: Annotated[IUserRepository, Depends(get_user_repository)]) -> UserService:
    return UserService(repo)
