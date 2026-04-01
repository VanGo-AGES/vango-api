from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DependentCreate(BaseModel):
    name: str = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field cannot be empty or only whitespace")
        return v


class DependentUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == "":
            raise ValueError("name não pode ser vazio ou conter apenas espaços")
        return v


class DependentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    guardian_id: UUID
    name: str
    created_at: datetime
