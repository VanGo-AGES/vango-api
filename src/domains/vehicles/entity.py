import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plate: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    driver = relationship("UserModel", back_populates="vehicles")
