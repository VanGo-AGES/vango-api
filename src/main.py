import sys
import traceback
from contextlib import asynccontextmanager

import firebase_admin
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from firebase_admin import credentials
from sqlalchemy import text

from src.config import settings
from src.domains.dependents.controller import router as dependent_controller
from src.domains.users.controller import router as user_controller
from src.domains.users.entity import UserModel
from src.domains.vehicles.controller import router as vehicle_controller
from src.infrastructure.database import Base, engine

_ = UserModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicialização do Firebase
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
            print("FIREBASE: Inicializado com sucesso.")
        except Exception as e:
            print(f"FIREBASE ERROR: Falha ao carregar credenciais: {e}")

    # 2. Inicialização do PostgreSQL 16
    try:
        # Diagnóstico: Lista quais tabelas o SQLAlchemy detectou
        print(f"DEBUG: Tabelas detectadas para criação: {list(Base.metadata.tables.keys())}")

        # Teste rápido de conectividade
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("DATABASE: Conexão estabelecida e tabelas sincronizadas!")
    except Exception as e:
        print(f"DATABASE ERROR: Falha ao conectar ou criar tabelas: {e}")

    yield

    # 3. Shutdown
    engine.dispose()
    print("INFRA: Conexões de banco encerradas.")


app = FastAPI(
    title=settings.app_name,
    description="API para gestão de transporte escolar (VanGo)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    traceback.print_exc(file=sys.stderr)

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
    )


app.include_router(user_controller)
app.include_router(vehicle_controller)
app.include_router(dependent_controller)


@app.get("/health", tags=["Infrastructure"])
def health_check() -> dict[str, str]:
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    return {"status": "ok", "database": db_status, "environment": "development"}


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": f"Bem-vindo à {settings.app_name}. Acesse /docs para a documentação interativa."}
