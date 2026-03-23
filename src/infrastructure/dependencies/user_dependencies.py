from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domains.users.repository import IPasswordHasher, IUserRepository
from src.domains.users.service import UserService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.user_repository import PasswordHasherImpl, UserRepositoryImpl

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DatabaseSession) -> IUserRepository:
    return UserRepositoryImpl(db)


def get_password_hasher() -> IPasswordHasher:
    return PasswordHasherImpl()


def get_user_service(
    repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> UserService:
    return UserService(repo, password_hasher)
