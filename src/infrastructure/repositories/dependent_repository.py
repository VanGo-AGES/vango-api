from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.dependents.entity import DependentModel
from src.domains.dependents.repository import IDependentRepository


class DependentRepositoryImpl(IDependentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, dependent: DependentModel) -> DependentModel:
        self.session.add(dependent)
        self.session.commit()
        self.session.refresh(dependent)
        return dependent

    def get_by_id(self, dependent_id: UUID) -> DependentModel | None:
        pass

    def get_by_guardian_id(self, guardian_id: UUID) -> list[DependentModel]:
        pass

    def update(self, dependent_id: UUID, data: dict) -> DependentModel | None:
        pass

    def delete(self, dependent_id: UUID) -> bool:
        pass
