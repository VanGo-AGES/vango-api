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
