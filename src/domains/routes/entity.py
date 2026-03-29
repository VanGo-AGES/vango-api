import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, SmallInteger, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class RouteModel(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    origin_address_id = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    destination_address_id = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=False)
    name = mapped_column(String, nullable=False)
    recurrence = mapped_column(String, nullable=False)
    max_passengers = mapped_column(SmallInteger, nullable=False)
    expected_time = mapped_column(Time(timezone=True), nullable=False)
    status = mapped_column(String, nullable=False)
    invite_code = mapped_column(String, unique=True, nullable=False)
    route_type = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    driver = relationship("User", back_populates="routes")
    origin_address = relationship("Address", foreign_keys=[origin_address_id])
    destination_address = relationship("Address", foreign_keys=[destination_address_id])
    passengers = relationship("RoutePassenger", back_populates="route", cascade="all, delete-orphan")
