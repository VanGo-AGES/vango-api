"""US07 — StopModel.

Representa uma parada (stop) de uma rota. Uma stop é criada quando um passageiro
é aceito na rota (endereço informado pelo passageiro) e removida quando o
passageiro é removido.
"""

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class StopModel(Base):
    __tablename__ = "stops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    route_passanger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("route_passangers.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "embarque" | "desembarque"
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # relationships
    route = relationship("RouteModel", back_populates="stops")
    address = relationship("AddressModel")
    route_passanger = relationship("RoutePassangerModel", back_populates="stop", uselist=False)
