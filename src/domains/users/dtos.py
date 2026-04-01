from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
    name: str | None = Field(..., min_length=3, max_length=255, example="John Doe")
    email: EmailStr | None = Field(..., example="john.doe@example.com")
    phone: str | None = Field(..., min_length=8, max_length=20, example="54999999999")
    password: str | None = Field(..., min_length=6, example="senha_segura123")
    cpf: str | None = Field(default=None, min_length=1, json_schema_extra={"example": "999.999.999-99"})
    photo_url: str | None = Field(default=None)
    # Apesar da task dizer nenhum optional, cpf e photo_url são optional no create
    # Trouxe aqui como optional também para não ficar inconsistente

    @model_validator(mode="before")
    @classmethod
    def email_normalization(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        email = data.get("email")
        if isinstance(email, str):
            data["email"] = email.strip().lower()
        return data

    @model_validator(mode="before")
    def optionals_not_empty_string(cls, data: object) -> object:
        if isinstance(data, dict):
            for field, value in data.items():
                if isinstance(value, str) and not value.strip():
                    raise ValueError(f"Campo '{field}' inválido (vazio).")
        return data
