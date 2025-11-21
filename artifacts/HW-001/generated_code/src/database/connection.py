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
        self.echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
        
    def get_engine_kwargs(self) -> dict:
        """
        Get SQLAlchemy engine configuration parameters.
        
        Returns:
            dict: Engine configuration parameters
        """
        kwargs = {
            "echo": self.echo,
            "future": True,
        }
        
        # SQLite-specific configuration
        if self.database_url.startswith("sqlite"):
            kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                }
            })
        else:
            # PostgreSQL/MySQL configuration
            kwargs.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "pool_pre_ping": True,
            })
            
        return kwargs


def create_database_engine(config: Optional[DatabaseConfig] = None) -> Engine:
    """
    Create and configure SQLAlchemy database engine.
    
    Args:
        config: Database configuration object. If None, creates default config.
        
    Returns:
        Engine: Configured SQLAlchemy engine
        
    Raises:
        SQLAlchemyError: If engine creation fails
    """
    if config is None:
        config = DatabaseConfig()
        
    try:
        engine = create_engine(
            config.database_url,
            **config.get_engine_kwargs()
        )
        
        # Add connection event listeners
        _setup_engine_events(engine)
        
        logger.info(f"Database engine created successfully: {config.database_url}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise SQLAlchemyError(f"Database engine creation failed: {e}") from e


def _setup_engine_events(engine: Engine) -> None:
    """
    Set up SQLAlchemy engine event listeners.
    
    Args:
        engine: SQLAlchemy engine to configure
    """
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign key constraints for SQLite connections."""
        if engine.url.drivername == "sqlite":
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
    @event.listens_for(engine, "engine_connect")
    def receive_engine_connect(conn, branch):
        """Log database connections."""
        logger.debug("Database connection established")


def initialize_database(config: Optional[DatabaseConfig] = None) -> None:
    """
    Initialize database connection and session factory.
    
    Args:
        config: Database configuration object. If None, creates default config.
        
    Raises:
        SQLAlchemyError: If database initialization fails
    """
    global _engine, _session_factory
    
    try:
        _engine = create_database_engine(config)
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise SQLAlchemyError(f"Database initialization failed: {e}") from e


def create_tables() -> None:
    """
    Create all database tables defined in models.
    
    Raises:
        SQLAlchemyError: If table creation fails
    """
    if _engine is None:
        raise SQLAlchemyError("Database not initialized. Call initialize_database() first.")
        
    try:
        Base.metadata.create_all(bind=_engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise SQLAlchemyError(f"Table creation failed: {e}") from e


def drop_tables() -> None:
    """
    Drop all database tables.
    
    Raises:
        SQLAlchemyError: If table dropping fails
    """
    if _engine is None:
        raise SQLAlchemyError("Database not initialized. Call initialize_database() first.")
        
    try:
        Base.metadata.drop_all(bind=_engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise SQLAlchemyError(f"Table dropping failed: {e}") from e


def get_session() -> Session:
    """
    Create a new database session.
    
    Returns:
        Session: SQLAlchemy database session
        
    Raises:
        SQLAlchemyError: If session creation fails
    """
    if _session_factory is None:
        raise SQLAlchemyError("Database not initialized. Call initialize_database() first.")
        
    try:
        return _session_factory()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise SQLAlchemyError(f"Session creation failed: {e}") from e


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.
    
    Yields:
        Session: SQLAlchemy database session
        
    Raises:
        SQLAlchemyError: If session operations fail
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise SQLAlchemyError(f"Database operation failed: {e}") from e
    finally:
        session.close()


def close_database() -> None:
    """
    Close database connections and clean up resources.
    """
    global _engine, _session_factory
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
        
    _session_factory = None
    logger.info("Database connections closed")


def get_engine() -> Engine:
    """
    Get the current database engine.