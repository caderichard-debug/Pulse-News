from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.db_metadata import configure_sqlmodel_metadata
from app.database import _normalize_database_url_for_psycopg2

# Bind metadata to app schema before any table=True models load.
configure_sqlmodel_metadata()

# Import SQLModel and all models
from sqlmodel import SQLModel
from app.models import (
    Source,
    Topic,
    Article,
    ArticleAnalysis,
    Framework,
    User,
    Newsletter,
    SourceTopicLink,
    ArticleTopicLink,
    NewsletterArticle,
    ArticleFrameworkLink,
    UserTopicPreference,
    UserSourceSubscription,
    StatisticVerification,
    ArticleCluster,
    ArticleClusterMember,
    ArticleContext,
    SourceCredibilityRating,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with environment variable if available
database_url = _normalize_database_url_for_psycopg2(settings.database_url)
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = SQLModel.metadata

_isolated = bool((settings.supabase_db_schema or "").strip())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    configure_kwargs = dict(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    if _isolated:
        configure_kwargs["version_table_schema"] = settings.supabase_db_schema
        configure_kwargs["include_schemas"] = True

    context.configure(**configure_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    configure_kwargs = dict(
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    if _isolated:
        configure_kwargs["version_table_schema"] = settings.supabase_db_schema
        configure_kwargs["include_schemas"] = True

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            **configure_kwargs,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
