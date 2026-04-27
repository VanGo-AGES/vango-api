"""Implementação SQLAlchemy do IAbsenceRepository.

US09-TK04 cobre find_by_route_and_date (usado pelo start_trip).
US06-TK18 estende com save/find_for_route_passanger_on_date (criação de
Absence pelo passageiro/guardian a partir da tela 2.3).
"""

from datetime import datetime, time
from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.trips.entity import AbsenceModel
from src.domains.trips.repository import IAbsenceRepository


class AbsenceRepositoryImpl(IAbsenceRepository):
    def __init__(self, session: Session):
        self.session = session

    # US09-TK04
    def find_by_route_and_date(self, route_id: UUID, absence_date: datetime) -> list[AbsenceModel]:
        pass

    # US06-TK18
    def save(self, absence: AbsenceModel) -> AbsenceModel:
        self.session.add(absence)
        self.session.commit()
        self.session.refresh(absence)
        return absence

    # US06-TK18
    def find_for_route_passanger_on_date(
        self,
        route_passanger_id: UUID,
        absence_date: datetime,
    ) -> AbsenceModel | None:
        tzinfo = absence_date.tzinfo
        start_of_day = datetime.combine(absence_date.date(), time.min, tzinfo=tzinfo)
        end_of_day = datetime.combine(absence_date.date(), time.max, tzinfo=tzinfo)

        return (
            self.session.query(AbsenceModel)
            .filter(
                AbsenceModel.route_passanger_id == route_passanger_id,
                AbsenceModel.absence_date >= start_of_day,
                AbsenceModel.absence_date <= end_of_day,
            )
            .first()
        )
