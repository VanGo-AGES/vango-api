from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehicleCreate(BaseModel):
    plate: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0, le=20)
    notes: str | None = None

    @field_validator("plate")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field cannot be empty or only whitespace")
        return v


class VehicleUpdate(BaseModel):
    plate: str | None = Field(default=None, min_length=1)
    capacity: int | None = Field(default=None, gt=0, le=20)
    notes: str | None = None


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID
    plate: str | None
    capacity: int
    notes: str | None
    status: bool
    created_at: datetime
