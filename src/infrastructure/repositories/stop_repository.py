"""US07 — Implementação SQLAlchemy do IStopRepository."""

from uuid import UUID

from sqlalchemy.orm import Session

from src.domains.stops.entity import StopModel
from src.domains.stops.repository import IStopRepository


class StopRepositoryImpl(IStopRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, stop: StopModel) -> StopModel:
        """Persiste uma stop nova ou atualizada e retorna a instância persistida."""
        self.session.add(stop)
        self.session.flush()
        self.session.commit()
        self.session.refresh(stop)
        return stop

    def find_by_id(self, stop_id: UUID) -> StopModel | None:
        """Retorna a stop pelo id, ou None se não existir."""
        return self.session.get(StopModel, stop_id)

    def find_by_route_id(self, route_id: UUID) -> list[StopModel]:
        """Retorna as stops de uma rota ordenadas por order_index."""
        return self.session.query(StopModel).filter(StopModel.route_id == route_id).order_by(StopModel.order_index).all()

    def find_by_route_passanger_id(self, rp_id: UUID) -> StopModel | None:
        """Retorna a stop associada a um vínculo route_passanger (1-1), ou None."""
        return self.session.query(StopModel).filter(StopModel.route_passanger_id == rp_id).first()

    def delete_by_route_passanger_id(self, rp_id: UUID) -> bool:
        """Deleta a stop associada a um route_passanger. Retorna True se removeu."""
        stop = self.session.query(StopModel).filter(StopModel.route_passanger_id == rp_id).first()
        if stop is None:
            return False
        self.session.delete(stop)
        self.session.flush()
        self.session.commit()
        return True
