from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# 1. O que a API RECEBE (Entrada)
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone: str = Field(..., min_length=8, max_length=20, example="54999999999")
    password: str = Field(..., min_length=6, example="senha_segura123")

    # Você pode definir um valor padrão ou exigir que venha do front
    role: str = Field(default="guardian", pattern="^(driver|passenger|guardian)$")

    # Opcional — obrigatório apenas para motoristas no fluxo de cadastro
    cpf: str | None = Field(default=None, json_schema_extra={"example": "999.999.999-99"})
    photo_url: str | None = None


# 2. O que a API DEVOLVE (Saída)
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    phone: str
    role: str
    cpf: str | None = None
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    password: str | None = None
    cpf: str | None = None
    photo_url: str | None = None
