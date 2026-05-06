"""US06 — DTOs do domínio absences.

Usados pelo fluxo de aviso de ausência do passageiro/guardian na tela 2.3.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateAbsenceRequest(BaseModel):
    """Payload enviado pelo passageiro (ou guardian) pra avisar ausência numa rota."""

    route_id: uuid.UUID
    absence_date: date
    dependent_id: uuid.UUID | None = None
    reason: str | None = Field(default=None, max_length=255)


class AbsenceResponse(BaseModel):
    """Representação de uma ausência persistida."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID | None = None
    route_passanger_id: uuid.UUID
    absence_date: datetime
    reason: str | None = None
    created_at: datetime


class RouteAbsenceResponse(BaseModel):
    """Ausência de um passageiro numa rota, vista pelo motorista."""

    route_passanger_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    dependent_id: uuid.UUID | None
    dependent_name: str | None
    absence_date: datetime
    reason: str | None
