from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.users.entity import UserModel
from src.domains.users.repository import IUserRepository


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
