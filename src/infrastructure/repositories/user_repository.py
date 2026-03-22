from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.entity import UserModel
from src.domains.users.repository import IPasswordHasher, IUserRepository
from src.infrastructure.security import hash_password, verify_password


class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: UserModel) -> UserModel:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def find_by_email(self, email: str) -> UserModel | None:
        return self.session.query(UserModel).filter(UserModel.email == email).first()

    def find_by_id(self, user_id: UUID) -> UserModel | None:
        return self.session.query(UserModel).filter(UserModel.id == user_id).first()


class PasswordHasherImpl(IPasswordHasher):
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
