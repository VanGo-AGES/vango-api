"""US09 — Implementação SQLAlchemy do IAbsenceRepository.

TK04 cobre: find_by_route_and_date.

Apenas o suficiente pra o start_trip conseguir consultar as faltas avisadas
para o dia. Criação de Absence (fluxo do passageiro/guardian) fica para outra
US (US11/US12).
"""

from datetime import datetime
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
