from abc import ABC, abstractmethod
from uuid import UUID

from .entity import UserModel


class IUserRepository(ABC):
    @abstractmethod
    def save(self, user: UserModel) -> UserModel:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> UserModel | None:
        pass

    @abstractmethod
    def find_by_id(self, user_id: UUID) -> UserModel | None:
        pass

    @abstractmethod
    def update(self, user_id: UUID, data: dict) -> UserModel | None:
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        pass

    @abstractmethod
    def find_all(self) -> list[UserModel]:
        pass


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass
