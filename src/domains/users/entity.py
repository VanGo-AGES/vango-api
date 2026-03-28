import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User(name={self.name}, role={self.role})>"

    # relationships
    dependents = relationship("DependentModel", back_populates="guardian", cascade="all, delete-orphan")
    vehicles = relationship("VehicleModel", back_populates="driver", cascade="all, delete-orphan")
    addresses = relationship("AddressModel", back_populates="user", cascade="all, delete-orphan")
    routes = relationship("RouteModel", back_populates="driver", cascade="all, delete-orphan")
