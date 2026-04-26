from sqlmodel import create_engine, Session, SQLModel
import time
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError
from typing import Generator, Optional, Tuple
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit, urlparse, urlunparse
import logging
from dotenv import load_dotenv
from .config import settings
from .db_metadata import configure_sqlmodel_metadata

load_dotenv()
logger = logging.getLogger(__name__)

# Pin metadata to app schema before any route imports models (when configured).
configure_sqlmodel_metadata()

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


def _percent_encode_userinfo_in_database_url(url: str) -> str:
    """
    Re-encode username and password for libpq/psycopg2.

    Passwords with ``+``, ``=``, ``@``, etc. must be percent-encoded in the URI;
    otherwise ``+`` is often misread and authentication fails against Supabase pooler.
    """
    try:
        p = urlparse(url)
    except Exception:
        return url
    if p.scheme not in ("postgresql", "postgres"):
        return url
    if not p.hostname or not p.username:
        return url
    user_raw = unquote(p.username)
    if p.password is not None:
        pass_raw = unquote(p.password)
        userinfo = f"{quote(user_raw)}:{quote(pass_raw)}"
    else:
        userinfo = quote(user_raw)
    host = p.hostname
    if p.port:
        netloc = f"{userinfo}@{host}:{p.port}"
    else:
        netloc = f"{userinfo}@{host}"
    rebuilt = urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    if rebuilt != url:
        logger.info("Re-encoded DATABASE_URL userinfo for safe libpq parsing (special characters in password)")
    return rebuilt


def prepare_database_url_for_engine(url: str) -> str:
    """Normalize schema query param and percent-encode credentials for psycopg2."""
    return _percent_encode_userinfo_in_database_url(_normalize_database_url_for_psycopg2(url))


def _validate_supabase_pooler_username(url: str) -> None:
    """
    Supabase pooler hosts reject a bare ``postgres`` login; the username must include
    the project ref (e.g. ``postgres.<ref>`` or ``app_pulse_rw.<ref>``).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return
    host = (parsed.hostname or "").lower()
    if "pooler.supabase.com" not in host:
        return
    user = parsed.username or ""
    if not user:
        raise RuntimeError(
            f"DATABASE_URL points at Supabase pooler ({host}) but has no username. "
            "Use postgres.<PROJECT_REF> or app_<role>_<PROJECT_REF> from Dashboard → Connect → Session pooler."
        )
    if "." not in user:
        ref = (settings.supabase_project_ref or "").strip() or "<PROJECT_REF>"
        raise RuntimeError(
            f"DATABASE_URL uses Supabase Session pooler ({host}) but username {user!r} is not tenant-qualified. "
            f"Use postgres.{ref} or app_pulse_rw.{ref} (replace with your project ref from the Supabase dashboard URL). "
            "Dashboard: Project Settings → Database → Connect → Session pooler. "
            "A bare 'postgres' user fails authentication on the pooler."
        )


# Create engine with SQLModel
_prepared_url = prepare_database_url_for_engine(DATABASE_URL)
_validate_supabase_pooler_username(_prepared_url)
engine = create_engine(_prepared_url, echo=True)  # echo=True for development


def _assert_isolation_on_connect(dbapi_conn, _connection_record) -> None:
    """Fail fast if pooler/DSN dropped search_path or wrong role (Supabase isolation)."""
    expected_schema = (settings.supabase_db_schema or "").strip()
    if not expected_schema:
        return
    cur = dbapi_conn.cursor()
    cur.execute("SELECT current_user, current_database(), current_schemas(true)")
    row = cur.fetchone()
    cur.close()
    if not row:
        raise RuntimeError("Isolation check: empty result from current_user/current_schemas")
    user, db, schemas = row[0], row[1], row[2]
    expected_role = (settings.supabase_db_role or "").strip()
    if expected_role and user != expected_role:
        raise RuntimeError(
            f"DB connected as {user!r}, expected {expected_role!r} "
            f"(set SUPABASE_DB_ROLE in env or clear it to skip role check)"
        )
    # psycopg2 returns list for array types; normalize to list of str
    path_list: list[str]
    if schemas is None:
        path_list = []
    elif isinstance(schemas, (list, tuple)):
        path_list = [str(s) for s in schemas]
    else:
        path_list = [str(s) for s in str(schemas).strip("{}").split(",") if s]
    if not path_list or path_list[0] != expected_schema:
        raise RuntimeError(
            f"search_path head is {path_list!r}, expected {expected_schema!r} first "
            f"(check DATABASE_URL options=-csearch_path=... and Session Pooler port 5432)"
        )
    logger.info("DB isolation OK: user=%s db=%s search_path=%s", user, db, path_list)


if settings.supabase_db_schema:
    event.listen(engine, "connect", _assert_isolation_on_connect)


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


def health_db_ping() -> Tuple[bool, Optional[str]]:
    """
    Lightweight connectivity check for /health when schema isolation is enabled.
    Returns (ok, error_message).
    """
    if not settings.supabase_db_schema:
        return True, None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)
