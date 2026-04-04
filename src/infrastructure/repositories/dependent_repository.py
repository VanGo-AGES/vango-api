from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.dependents.entity import DependentModel
from src.domains.dependents.repository import IDependentRepository


class DependentRepositoryImpl(IDependentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, dependent: DependentModel) -> DependentModel:
        pass

    def get_by_id(self, dependent_id: UUID) -> DependentModel | None:
        return self.session.query(DependentModel).filter(DependentModel.id == dependent_id).first()

    def get_by_guardian_id(self, guardian_id: UUID) -> list[DependentModel]:
        return self.session.query(DependentModel).filter(DependentModel.guardian_id == guardian_id).all()

    def update(self, dependent_id: UUID, data: dict) -> DependentModel | None:
        dependent = self.get_by_id(dependent_id)
        if dependent is None:
            return None

        for key, value in data.items():
            setattr(dependent, key, value)

        self.session.commit()
        self.session.refresh(dependent)
        return dependent

    def delete(self, dependent_id: UUID) -> bool:
        dependent = self.get_by_id(dependent_id)
        if dependent is None:
            return False

        self.session.delete(dependent)
        self.session.commit()
        return True
