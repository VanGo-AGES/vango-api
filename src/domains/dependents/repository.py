from abc import ABC, abstractmethod
from uuid import UUID

from .entity import DependentModel


class IDependentRepository(ABC):
    @abstractmethod
    def create(self, dependent: DependentModel) -> DependentModel:
        pass

    @abstractmethod
    def get_by_id(self, dependent_id: UUID) -> DependentModel | None:
        pass

    @abstractmethod
    def get_by_guardian_id(self, guardian_id: UUID) -> list[DependentModel]:
        pass

    @abstractmethod
    def update(self, dependent_id: UUID, data: dict) -> DependentModel | None:
        pass

    @abstractmethod
    def delete(self, dependent_id: UUID) -> bool:
        pass
