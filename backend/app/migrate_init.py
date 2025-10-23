"""
Smart migration initialization for production databases.

This script handles both scenarios:
1. New database: Runs migrations normally
2. Existing database without alembic_version: Stamps current state, then migrates

This prevents "relation already exists" errors on production databases that
were created before Alembic was introduced.
"""

import logging
import subprocess
import sys
from sqlalchemy import text, inspect
from .database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def check_alembic_version_exists() -> bool:
    """Check if alembic_version table exists."""
    return check_table_exists("alembic_version")


def get_current_alembic_version() -> str | None:
    """Get the current alembic version from the database."""
    if not check_alembic_version_exists():
        return None

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        return row[0] if row else None


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    logger.info(f"{description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} complete")
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e}")
        if e.stderr:
            logger.error(e.stderr)
        return False


def drop_all_tables():
    """Drop all tables and start fresh. USE WITH CAUTION!"""
    logger.warning("⚠️  FORCE REBUILD: Dropping all tables...")

    with engine.connect() as conn:
        # Drop all tables
        conn.execute(text("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """))
        conn.commit()

    logger.info("✓ All tables dropped. Database reset to empty state.")


def init_migrations():
    """
    Initialize Alembic migrations intelligently.

    Strategy:
    1. If FORCE_REBUILD=true: Drop everything and rebuild from scratch (ONE TIME ONLY)
    2. If alembic_version exists: Run migrations normally
    3. If tables exist but no alembic_version: Stamp with initial migration, then upgrade
    4. If no tables: Run migrations normally (creates everything)
    """
    import os

    logger.info("=== Initializing Database Migrations ===")

    # Check for force rebuild flag (should be set in render.yaml for next deployment only)
    force_rebuild = os.getenv("FORCE_REBUILD", "false").lower() == "true"

    if force_rebuild:
        logger.warning("🔥 FORCE_REBUILD=true detected - This will drop all tables!")
        drop_all_tables()
        logger.info("Fresh database after force rebuild - running all migrations")
        if not run_command(["alembic", "upgrade", "head"], "Creating database schema"):
            sys.exit(1)
        logger.info("=== Migration initialization complete ===\n")
        return

    # Check current state
    has_alembic_version = check_alembic_version_exists()
    has_topics_table = check_table_exists("topics")

    if has_alembic_version:
        # Normal case: Alembic already tracking migrations
        current_version = get_current_alembic_version()
        logger.info(f"Alembic version tracking exists (current: {current_version})")
        logger.info("Running normal migration upgrade...")

        # Try normal upgrade first, if it fails due to multiple heads, upgrade all heads
        if not run_command(["alembic", "upgrade", "head"], "Upgrading to latest migration"):
            logger.warning("Multiple migration heads detected, upgrading all heads...")
            if not run_command(["alembic", "upgrade", "heads"], "Upgrading all migration heads"):
                sys.exit(1)

    elif has_topics_table:
        # Production case: Tables exist but no alembic_version
        logger.info("⚠️  Database has tables but no Alembic version tracking")
        logger.info("This is a production database created before migrations were added")

        # Stamp with the initial migration (without running it)
        logger.info("Stamping database with initial schema version...")
        if not run_command(
            ["alembic", "stamp", "20251009_000001"],
            "Stamping with initial migration"
        ):
            sys.exit(1)

        # Now run any new migrations
        logger.info("Running any new migrations...")
        if not run_command(["alembic", "upgrade", "head"], "Upgrading to latest migration"):
            sys.exit(1)

    else:
        # Fresh database: No tables, no alembic_version
        logger.info("Fresh database detected - running all migrations")
        if not run_command(["alembic", "upgrade", "head"], "Creating database schema"):
            sys.exit(1)

    logger.info("=== Migration initialization complete ===\n")


if __name__ == "__main__":
    try:
        init_migrations()
    except Exception as e:
        logger.error(f"Migration initialization failed: {e}", exc_info=True)
        sys.exit(1)
