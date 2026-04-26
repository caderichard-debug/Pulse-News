from sqlmodel import create_engine, Session, SQLModel
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from typing import Generator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import os
import logging
from dotenv import load_dotenv
from .config import settings

load_dotenv()
logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment variable, fallback to default
DATABASE_URL = settings.database_url


def _normalize_database_url_for_psycopg2(url: str) -> str:
    """
    Convert non-standard ?schema=<name> URLs into psycopg2-compatible options.

    psycopg2 rejects `schema` as an unknown DSN option, but accepts:
    ?options=-csearch_path=<schema>,public
    """
    parts = urlsplit(url)
    params = parse_qsl(parts.query, keep_blank_values=True)
    schema = None
    filtered: list[tuple[str, str]] = []

    for key, value in params:
        if key == "schema" and value:
            schema = value
            continue
        filtered.append((key, value))

    if schema:
        options_set = False
        updated: list[tuple[str, str]] = []
        for key, value in filtered:
            if key == "options":
                value = f"{value} -csearch_path={schema},public".strip()
                options_set = True
            updated.append((key, value))
        if not options_set:
            updated.append(("options", f"-csearch_path={schema},public"))
        filtered = updated
        logger.info("Normalized DATABASE_URL schema parameter to PostgreSQL search_path option")

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(filtered), parts.fragment))


# Create engine with SQLModel
engine = create_engine(_normalize_database_url_for_psycopg2(DATABASE_URL), echo=True)  # echo=True for development


def create_db_and_tables():
    """Create all database tables"""
    #SQLModel.metadata.create_all(engine)

    max_retries = 30
    for attempt in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            logger.info("DB connected and tables created!")
            break
        except OperationalError as e:
            logger.info(f"OperationalError: {e}")
            logger.info(f"Database not ready, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(1)
    else:
        raise RuntimeError(f"Database did not become ready in time.\nURL: {DATABASE_URL}")
    

def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database sessions in FastAPI routes"""
    with Session(engine) as session:
        yield session

