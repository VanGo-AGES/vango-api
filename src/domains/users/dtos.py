from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# 1. O que a API RECEBE (Entrada)
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone: str = Field(..., min_length=8, max_length=20, example="54999999999")
    password: str = Field(..., min_length=6, example="senha_segura123")

    # Você pode definir um valor padrão ou exigir que venha do front
    role: str = Field(default="guardian", pattern="^(driver|passenger|guardian)$")


# 2. O que a API DEVOLVE (Saída)
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str
    role: str
    created_at: datetime
    updated_at: datetime

    # Necessário para o Pydantic ler o objeto do SQLAlchemy (UserModel)
    class Config:
        from_attributes = True
