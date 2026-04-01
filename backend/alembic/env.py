import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from alembic import context

# Add backend directory to path so model imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Alembic Config object
config = context.config

# Set sqlalchemy.url from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/oneclass")
config.set_main_option("sqlalchemy.url", database_url)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base and all models for autogenerate support
from shared.database import Base

# Import all shared models (registers them with Base.metadata)
import shared.models.platform
import shared.models.platform_user
import shared.models.academic
import shared.models.finance
import shared.models.sis
import shared.models.audit_log

# Import service-level models
import services.finance.models

target_metadata = Base.metadata

# Schemas to include in autogenerate
SCHEMAS = ["public", "platform", "sis", "academic", "finance", "analytics", "audit"]


def include_name(name, type_, parent_names):
    """Filter which schemas to include in autogenerate."""
    if type_ == "schema":
        return name in SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create schemas if they don't exist
        for schema in SCHEMAS:
            if schema != "public":
                connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema="public",
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
