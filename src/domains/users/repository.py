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

    # US12-TK01
    @abstractmethod
    def update_push_token(self, user_id: UUID, token: str) -> UserModel | None:
        """Persiste o FCM push token no registro do usuário.

        Retorna o UserModel atualizado, ou None se o usuário não existir.
        """
        pass

    # US20-TK02
    @abstractmethod
    def soft_delete_and_anonymize(self, user_id: UUID) -> bool:
        """Marca o usuário como inativo (deleted_at + is_active=False) e
        anonimiza os dados pessoais (name/email/phone/cpf/photo_url/push_token),
        preservando o id para integridade do histórico. Retorna False se não existir.
        """
        pass


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass
