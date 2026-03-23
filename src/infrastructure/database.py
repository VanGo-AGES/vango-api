from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings

engine = create_engine(settings.database_url, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Extendivel
class Base(DeclarativeBase):
    pass


# DI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
