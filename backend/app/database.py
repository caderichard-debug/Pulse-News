from sqlmodel import create_engine, Session, SQLModel
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment variable, fallback to default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db:5432/news_db"
)

# Create engine with SQLModel
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for development


def create_db_and_tables():
    """Create all database tables"""
    #SQLModel.metadata.create_all(engine)

    max_retries = 30
    for attempt in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            logger("DB connected and tables created!")
            break
        except OperationalError as e:
            logger("OperationalError: ", e)
            logger(f"Database not ready, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(1)
    else:
        raise RuntimeError(f"Database did not become ready in time.\nURL: {DATABASE_URL}")
    

def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database sessions in FastAPI routes"""
    with Session(engine) as session:
        yield session

