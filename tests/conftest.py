import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database import Base
from src.domains.users.entity import UserModel
from src.domains.vehicles.entity import VehicleModel
from src.domains.dependents.entity import DependentModel
from src.domains.addresses.entity import AddressModel
from src.domains.routes.entity import RouteModel
from src.domains.route_passangers.entity import RoutePassangerModel


# Engine de teste (SQLite em memória)
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mantém o banco vivo durante os testes
    )

    Base.metadata.create_all(engine)
    return engine


# Sessão por teste (com rollback)
@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
