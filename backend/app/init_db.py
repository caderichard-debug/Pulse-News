"""
Database initialization script for production deployment.

This script:
1. Waits for database to be ready
2. Seeds initial data (sources, topics, frameworks) if needed
3. Does NOT run initial scraping (that's handled by background jobs)

Usage:
    python -m app.init_db
"""

from .seed_data import seed_database
import logging

logger = logging.getLogger(__name__)


def init():
    """Initialize database with seed data only (no scraping)."""
    logger.info("Initializing database...")

    try:
        # Seed database (idempotent - won't duplicate data)
        seed_database()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise


if __name__ == "__main__":
    init()
