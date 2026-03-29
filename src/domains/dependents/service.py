from src.domains.dependents.dtos import DependentCreate, DependentUpdate
from src.domains.dependents.entity import DependentModel
from src.domains.dependents.repository import IDependentRepository


class DependentService:
    def __init__(self, repository: IDependentRepository):
        self.repository = repository

    def add_dependent(self, user_id: str, user_role: str, data: DependentCreate) -> DependentModel:
        pass

    def get_dependents(self, user_id: str) -> list[DependentModel]:
        pass

    def get_dependent(self, user_id: str, dependent_id: str) -> DependentModel:
        pass

    def update_dependent(self, user_id: str, dependent_id: str, data: DependentUpdate) -> DependentModel:
        pass

    def delete_dependent(self, user_id: str, dependent_id: str) -> None:
        pass
