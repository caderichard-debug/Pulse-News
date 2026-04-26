"""
Configure SQLModel metadata before any `table=True` models are imported.

Isolated Supabase deploys set SUPABASE_DB_SCHEMA=proj_<name> so all tables are
schema-qualified. Local/CI leave it unset so metadata stays default (public).
"""

from __future__ import annotations

import logging

from sqlalchemy import MetaData
from sqlmodel import SQLModel

from .config import settings

logger = logging.getLogger(__name__)


def configure_sqlmodel_metadata() -> None:
    """Bind SQLModel to an app schema when SUPABASE_DB_SCHEMA is set."""
    schema = (settings.supabase_db_schema or "").strip()
    if not schema:
        return
    if getattr(SQLModel.metadata, "schema", None) == schema:
        return
    SQLModel.metadata = MetaData(schema=schema)
    logger.info("SQLModel metadata bound to schema %r", schema)
