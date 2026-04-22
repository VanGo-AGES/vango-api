import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class RoutePassangerModel(Base):
    __tablename__ = "route_passangers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dependent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dependents.id", ondelete="CASCADE"), nullable=True
    )
    pickup_address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    route = relationship("RouteModel", back_populates="passengers")
    user = relationship("UserModel")
    dependent = relationship("DependentModel")
    pickup_address = relationship("AddressModel", foreign_keys=[pickup_address_id])
    # US07 — stop associada a este passageiro (a stop referencia o rp via FK)
    stop = relationship("StopModel", back_populates="route_passanger", uselist=False, cascade="all, delete-orphan")
    # US08 — dias em que o passageiro participa (cada schedule tem dia + endereço)
    schedules = relationship(
        "RoutePassangerScheduleModel",
        back_populates="route_passanger",
        cascade="all, delete-orphan",
    )
    # US09 — registros de execução (presença em viagens)
    trip_passangers = relationship(
        "TripPassangerModel",
        back_populates="route_passanger",
        cascade="all, delete-orphan",
    )
    # US09 — avisos de falta emitidos por este passageiro/guardian
    absences = relationship(
        "AbsenceModel",
        back_populates="route_passanger",
        cascade="all, delete-orphan",
    )
