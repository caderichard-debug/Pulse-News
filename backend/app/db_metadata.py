"""
Configure SQLModel metadata before any `table=True` models are imported.

If APP_DB_SCHEMA is set, all SQLModel tables are schema-qualified.
If unset, metadata stays default (public).
"""

from __future__ import annotations

import logging

from sqlalchemy import MetaData
from sqlmodel import SQLModel

from .config import settings

logger = logging.getLogger(__name__)


def configure_sqlmodel_metadata() -> None:
    """Bind SQLModel to an app schema when APP_DB_SCHEMA is set."""
    schema = (settings.app_db_schema or "").strip()
    if not schema:
        return
    if getattr(SQLModel.metadata, "schema", None) == schema:
        return
    SQLModel.metadata = MetaData(schema=schema)
    logger.info("SQLModel metadata bound to schema %r", schema)
