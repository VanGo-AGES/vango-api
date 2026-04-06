from src.domains.users.dtos import UserCreate, UserUpdate
from src.domains.users.entity import UserModel
from src.domains.users.errors import DuplicateEmailError, UserNotFoundError
from src.domains.users.repository import IPasswordHasher, IUserRepository


class UserService:
    def __init__(self, repository: IUserRepository, password_hasher: IPasswordHasher):
        self.repository = repository
        self.password_hasher = password_hasher

    def create_user(self, user_data: UserCreate) -> UserModel:
        # 1. Regra de Negócio: E-mail deve ser único
        existing_user = self.repository.find_by_email(user_data.email)
        if existing_user:
            raise DuplicateEmailError()

        # 2. Transformar DTO (Schema) em Entity (Model) + Hashing
        new_user = UserModel(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=self.password_hasher.hash(user_data.password),
            role=user_data.role,
            cpf=user_data.cpf,
            photo_url=user_data.photo_url,
        )

        # 3. Persistir via Repository
        return self.repository.save(new_user)

    def get_user(self, user_id: str) -> UserModel:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user

    def update_user(self, user_id: str, data: UserUpdate) -> UserModel:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        update_data = data.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = self.password_hasher.hash(update_data.pop("password"))

        self.repository.update(user_id, update_data)
        return self.repository.find_by_id(user_id)

    def delete_user(self, user_id: str) -> None:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        self.repository.delete(user_id)
