from datetime import UTC, datetime
from uuid import UUID, uuid4

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

    def update(self, user_id: UUID, data: dict) -> UserModel | None:
        user = self.find_by_id(user_id)
        if not user:
            return None

        for key, value in data.items():
            setattr(user, key, value)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: UUID) -> bool:
        user = self.find_by_id(user_id)
        if not user:
            return False

        self.session.delete(user)
        self.session.commit()
        return True

    def find_all(self) -> list[UserModel]:
        return self.session.query(UserModel).all()

    # US12-TK01
    def update_push_token(self, user_id: UUID, token: str) -> UserModel | None:
        user = self.find_by_id(user_id)
        if not user:
            return None

        user.push_token = token
        self.session.commit()
        self.session.refresh(user)
        return user

    # US20-TK02
    def soft_delete_and_anonymize(self, user_id: UUID) -> bool:
        user = self.find_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        user.name = f"deleted-{user.id}"
        user.email = f"deleted-{user.id}@example.com"
        user.phone = ""
        user.password_hash = hash_password(uuid4().hex)
        user.cpf = None
        user.photo_url = None
        user.push_token = None

        self.session.commit()
        self.session.refresh(user)
        return True


class PasswordHasherImpl(IPasswordHasher):
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
