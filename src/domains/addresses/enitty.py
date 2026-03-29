import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class AddressModel(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = mapped_column(String, nullable=False)
    street = mapped_column(String, nullable=False)
    number = mapped_column(String, nullable=False)
    neighborhood = mapped_column(String, nullable=False)
    zip = mapped_column(String(9), nullable=False)
    city = mapped_column(String, nullable=False)
    state = mapped_column(String, nullable=False)
    latitude = mapped_column(Float, nullable=False)
    longitude = mapped_column(Float, nullable=False)
    is_default = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    user = relationship("User", back_populates="addresses")
