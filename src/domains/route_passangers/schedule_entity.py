"""US08 — Entidade RoutePassangerScheduleModel.

Tabela route_passanger_schedules: define os dias e endereços específicos
em que um passageiro pega a van. Cada passageiro tem N schedules (um por
dia da semana em que participa), e cada schedule pode ter um endereço
diferente.
"""

import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class RoutePassangerScheduleModel(Base):
    __tablename__ = "route_passanger_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_passanger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("route_passangers.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String, nullable=False)

    # relationships
    route_passanger = relationship("RoutePassangerModel", back_populates="schedules")
    address = relationship("AddressModel", foreign_keys=[address_id])
