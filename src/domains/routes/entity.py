import uuid
from datetime import datetime, time

from sqlalchemy import UUID, DateTime, ForeignKey, SmallInteger, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class RouteModel(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    origin_address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    destination_address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    recurrence: Mapped[str] = mapped_column(String, nullable=False)
    max_passengers: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expected_time: Mapped[time] = mapped_column(Time(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    invite_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    route_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    driver = relationship("UserModel", back_populates="routes")
    origin_address = relationship("AddressModel", foreign_keys=[origin_address_id])
    destination_address = relationship("AddressModel", foreign_keys=[destination_address_id])
    passengers = relationship("RoutePassangerModel", back_populates="route", cascade="all, delete-orphan")
    # US07 — stops da rota (ordenadas por order_index)
    stops = relationship(
        "StopModel",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="StopModel.order_index",
    )
