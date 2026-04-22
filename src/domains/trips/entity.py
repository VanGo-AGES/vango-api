"""US09 — Execução de viagem.

Este módulo define as entidades que representam a execução (run) de uma rota
em um dia específico:

- TripModel: execução da rota (start, finish, veículo usado, status)
- TripPassangerModel: registro histórico por passageiro (presente/ausente,
  boarded_at, alighted_at)
- AbsenceModel: aviso prévio de falta do passageiro/guardian. É carregado
  por start_trip para pré-marcar trip_passengers ausentes.

Uma rota (RouteModel) é o trajeto base recorrente; uma trip é uma ocorrência
concreta dessa rota em um dia/horário. Cada trip tem zero-ou-mais
trip_passengers (um por vínculo aceito na rota naquele momento).
"""

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class TripModel(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    trip_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # "iniciada" | "finalizada" | "cancelada"
    total_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    route = relationship("RouteModel", back_populates="trips")
    vehicle = relationship("VehicleModel")
    trip_passangers = relationship(
        "TripPassangerModel",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    absences = relationship(
        "AbsenceModel",
        back_populates="trip",
        cascade="all, delete-orphan",
    )


class TripPassangerModel(Base):
    __tablename__ = "trip_passangers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    route_passanger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_passangers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)  # "pendente" | "presente" | "ausente"
    boarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alighted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    trip = relationship("TripModel", back_populates="trip_passangers")
    route_passanger = relationship("RoutePassangerModel", back_populates="trip_passangers")


class AbsenceModel(Base):
    __tablename__ = "absences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    route_passanger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_passangers.id", ondelete="CASCADE"), nullable=False
    )
    absence_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    trip = relationship("TripModel", back_populates="absences")
    route_passanger = relationship("RoutePassangerModel", back_populates="absences")
