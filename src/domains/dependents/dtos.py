from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DependentCreate(BaseModel):
    name: str


class DependentUpdate(BaseModel):
    name: str | None = None


class DependentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    guardian_id: UUID
    name: str
    created_at: datetime
