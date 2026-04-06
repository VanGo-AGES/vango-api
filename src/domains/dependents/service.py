import uuid

from src.domains.dependents.dtos import DependentCreate, DependentUpdate
from src.domains.dependents.entity import DependentModel
from src.domains.dependents.errors import DependentAccessDeniedError, DependentNotFoundError, DependentOwnershipError
from src.domains.dependents.repository import IDependentRepository


class DependentService:
    def __init__(self, repository: IDependentRepository):
        self.repository = repository

    def add_dependent(self, user_id: str, user_role: str, data: DependentCreate) -> DependentModel:
        if user_role == "driver":
            raise DependentAccessDeniedError()
        dependent = DependentModel(
            guardian_id=uuid.UUID(user_id),
            name=data.name,
        )
        return self.repository.create(dependent)

    def get_dependents(self, user_id: str) -> list[DependentModel]:
        return self.repository.get_by_guardian_id(uuid.UUID(user_id))

    def get_dependent(self, user_id: str, dependent_id: uuid.UUID) -> DependentModel:
        dependent = self.repository.get_by_id(dependent_id)
        if dependent is None:
            raise DependentNotFoundError()
        if str(dependent.guardian_id) != user_id:
            raise DependentOwnershipError()
        return dependent

    def update_dependent(self, user_id: str, dependent_id: uuid.UUID, data: DependentUpdate) -> DependentModel:
        dependent = self.repository.get_by_id(dependent_id)
        if dependent is None:
            raise DependentNotFoundError()
        if str(dependent.guardian_id) != user_id:
            raise DependentOwnershipError()
        return self.repository.update(dependent_id, data.model_dump(exclude_none=True))

    def delete_dependent(self, user_id: str, dependent_id: uuid.UUID) -> None:
        dependent = self.repository.get_by_id(dependent_id)
        if dependent is None:
            raise DependentNotFoundError()
        if str(dependent.guardian_id) != user_id:
            raise DependentOwnershipError()
        self.repository.delete(dependent_id)
