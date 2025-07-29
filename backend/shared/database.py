"""
Database Configuration and Connection Management
Handles database connections and session management for OneClass Platform
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/oneclass"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Metadata for schema management
metadata = MetaData()


def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database_schemas():
    """
    Create database schemas if they don't exist
    """
    try:
        with engine.connect() as connection:
            # Create schemas
            schemas = ["platform", "sis", "academic", "finance", "analytics"]
            for schema in schemas:
                connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                logger.info(f"Schema '{schema}' ensured")

            connection.commit()
            logger.info("All database schemas created successfully")

    except Exception as e:
        logger.error(f"Failed to create database schemas: {e}")
        raise


def init_database():
    """
    Initialize database with all tables and schemas
    """
    try:
        # Create schemas first
        create_database_schemas()

        # Import all models to register them with SQLAlchemy
        from .models import platform, academic, finance, sis

        # Create all tables for each schema
        platform.Base.metadata.create_all(bind=engine)
        academic.Base.metadata.create_all(bind=engine)
        finance.Base.metadata.create_all(bind=engine)
        sis.Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully with all schemas and tables")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db_session() -> Session:
    """
    Get a database session (alternative to dependency injection)
    """
    return SessionLocal()


def close_db_session(session: Session):
    """
    Close database session
    """
    session.close()


# Health check function
async def check_database_health() -> bool:
    """
    Check if database is accessible and healthy
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Async engine (assuming PostgreSQL with asyncpg driver)
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/oneclass"
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncSession:
    """
    Dependency to get async database session
    """
    async with AsyncSessionLocal() as session:
        yield session
