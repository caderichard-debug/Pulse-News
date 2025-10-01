from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Get DATABASE_URL from environment variable, fallback to default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db:5432/news_db"
)

# Create engine with SQLModel
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for development


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database sessions in FastAPI routes"""
    with Session(engine) as session:
        yield session

