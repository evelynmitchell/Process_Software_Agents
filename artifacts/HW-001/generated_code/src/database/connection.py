"""
SQLAlchemy database connection setup, session management, and base model configuration.

This module provides database connection management, session handling, and base model
configuration for SQLAlchemy ORM operations.

Component ID: COMP-010
Semantic Unit: SU-010

Author: ASP Code Agent
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# Configure logging
logger = logging.getLogger(__name__)

# Base class for all database models
Base = declarative_base()

# Global database engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self) -> None:
        """Initialize database configuration from environment variables."""
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "sqlite:///./hello_world.db"
        )
        self.echo_sql = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))


def create_database_engine(config: Optional[DatabaseConfig] = None) -> Engine:
    """
    Create and configure SQLAlchemy database engine.
    
    Args:
        config: Database configuration object. If None, creates default config.
        
    Returns:
        Engine: Configured SQLAlchemy engine
        
    Raises:
        SQLAlchemyError: If engine creation fails
        
    Example:
        >>> engine = create_database_engine()
        >>> engine.url.database
        './hello_world.db'
    """
    if config is None:
        config = DatabaseConfig()
    
    try:
        # Configure engine parameters based on database type
        engine_kwargs = {
            "echo": config.echo_sql,
            "future": True,  # Use SQLAlchemy 2.0 style
        }
        
        # SQLite-specific configuration
        if config.database_url.startswith("sqlite"):
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                }
            })
        else:
            # PostgreSQL/MySQL configuration
            engine_kwargs.update({
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
                "pool_timeout": config.pool_timeout,
                "pool_recycle": config.pool_recycle,
                "pool_pre_ping": True,  # Verify connections before use
            })
        
        engine = create_engine(config.database_url, **engine_kwargs)
        
        # Add connection event listeners
        _setup_engine_events(engine)
        
        logger.info(f"Database engine created successfully: {config.database_url}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise SQLAlchemyError(f"Database engine creation failed: {e}") from e


def _setup_engine_events(engine: Engine) -> None:
    """
    Set up database engine event listeners for connection management.
    
    Args:
        engine: SQLAlchemy engine to configure
    """
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Configure SQLite connection settings."""
        if engine.url.drivername == "sqlite":
            cursor = dbapi_connection.cursor()
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set journal mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    
    @event.listens_for(engine, "engine_connect")
    def log_connection(conn, branch):
        """Log database connections."""
        logger.debug("Database connection established")


def initialize_database(config: Optional[DatabaseConfig] = None) -> None:
    """
    Initialize the global database engine and session factory.
    
    Args:
        config: Database configuration object. If None, creates default config.
        
    Raises:
        SQLAlchemyError: If database initialization fails
        RuntimeError: If database is already initialized
        
    Example:
        >>> initialize_database()
        >>> get_engine() is not None
        True
    """
    global _engine, _session_factory
    
    if _engine is not None:
        raise RuntimeError("Database already initialized. Call close_database() first.")
    
    try:
        _engine = create_database_engine(config)
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        _engine = None
        _session_factory = None
        raise


def get_engine() -> Engine:
    """
    Get the global database engine.
    
    Returns:
        Engine: The global SQLAlchemy engine
        
    Raises:
        RuntimeError: If database is not initialized
        
    Example:
        >>> initialize_database()
        >>> engine = get_engine()
        >>> engine.url is not None
        True
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get the global session factory.
    
    Returns:
        sessionmaker: The global SQLAlchemy session factory
        
    Raises:
        RuntimeError: If database is not initialized
        
    Example:
        >>> initialize_database()
        >>> factory = get_session_factory()
        >>> session = factory()
        >>> isinstance(session, Session)
        True
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _session_factory


def create_session() -> Session:
    """
    Create a new database session.
    
    Returns:
        Session: New SQLAlchemy session
        
    Raises:
        RuntimeError: If database is not initialized
        SQLAlchemyError: If session creation fails
        
    Example:
        >>> initialize_database()
        >>> session = create_session()
        >>> session.is_active
        True
        >>> session.close()
    """
    try:
        session_factory = get_session_factory()
        session = session_factory()
        logger.debug("Database session created")
        return session
        
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise SQLAlchemyError(f"Session creation failed: {e}") from e


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.
    
    Yields:
        Session: Database session that will be automatically closed
        
    Raises:
        RuntimeError: If database is not initialized
        SQLAlchemyError: If session operations fail
        
    Example:
        >>> initialize_database()
        >>> with get_db_session() as session:
        ...     # Use session for database operations
        ...     result = session.execute("SELECT 1")
        ...