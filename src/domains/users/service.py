from fastapi import HTTPException, status

from src.domains.users.dtos import UserCreate
from src.domains.users.entity import UserModel
from src.domains.users.repository import IPasswordHasher, IUserRepository


class UserService:
    def __init__(self, repository: IUserRepository, password_hasher: IPasswordHasher):
        self.repository = repository
        self.password_hasher = password_hasher

    def create_user(self, user_data: UserCreate) -> UserModel:
        # 1. Regra de Negócio: E-mail deve ser único
        existing_user = self.repository.find_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este e-mail já está cadastrado.")

        # 2. Transformar DTO (Schema) em Entity (Model) + Hashing
        new_user = UserModel(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=self.password_hasher.hash(user_data.password),  # Senha protegida!
            role=user_data.role,
        )

        # 3. Persistir via Repository
        return self.repository.save(new_user)
