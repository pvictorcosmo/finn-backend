from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# Normalizar URL para o driver psycopg3 do SQLAlchemy
db_url = settings.database_url.replace("postgres://", "postgresql://", 1).replace(
    "postgresql://", "postgresql+psycopg://", 1
)
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
