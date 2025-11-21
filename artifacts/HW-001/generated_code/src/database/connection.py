"""
SQLAlchemy database connection setup, session management, and database initialization.

This module provides database connection management, session handling, and initialization
utilities for the Hello World API application.

Component ID: COMP-010
Semantic Unit: SU-010

Author: ASP Code Agent
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


# Configure logging
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self) -> None:
        """Initialize database configuration from environment variables."""
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "sqlite:///./hello_world.db"
        )
        self.echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
        self.pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
    def get_engine_kwargs(self) -> dict:
        """Get SQLAlchemy engine configuration parameters."""
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
                    "timeout": 20
                }
            })
        else:
            # PostgreSQL/MySQL configuration
            kwargs.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "pool_pre_ping": True
            })
            
        return kwargs


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None) -> None:
        """
        Initialize database manager.
        
        Args:
            config: Database configuration. If None, creates default config.
        """
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
        
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                class_=Session,
                expire_on_commit=False
            )
        return self._session_factory
        
    def _create_engine(self) -> Engine:
        """Create and configure SQLAlchemy engine."""
        try:
            engine_kwargs = self.config.get_engine_kwargs()
            engine = create_engine(self.config.database_url, **engine_kwargs)
            
            # Add event listeners
            self._setup_engine_events(engine)
            
            logger.info(f"Database engine created for URL: {self._mask_url(self.config.database_url)}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise DatabaseConnectionError(f"Failed to create database engine: {e}") from e
            
    def _setup_engine_events(self, engine: Engine) -> None:
        """Set up SQLAlchemy engine event listeners."""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and reliability."""
            if "sqlite" in str(engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                cursor.close()
                
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log database connection checkout."""
            logger.debug("Database connection checked out from pool")
            
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log database connection checkin."""
            logger.debug("Database connection returned to pool")
            
    def _mask_url(self, url: str) -> str:
        """Mask sensitive information in database URL for logging."""
        if "://" not in url:
            return url
            
        try:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                credentials, host_part = rest.split("@", 1)
                return f"{protocol}://***:***@{host_part}"
            return url
        except Exception:
            return "***masked***"
            
    def create_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            Session: New SQLAlchemy session
            
        Raises:
            DatabaseConnectionError: If session creation fails
        """
        try:
            session = self.session_factory()
            logger.debug("Database session created")
            return session
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            raise DatabaseConnectionError(f"Failed to create database session: {e}") from e
            
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup.
        
        Yields:
            Session: Database session
            
        Raises:
            DatabaseConnectionError: If session operations fail
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
            logger.debug("Database session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Database session rolled back due to error: {e}")
            raise
        finally:
            session.close()
            logger.debug("Database session closed")
            
    def init_database(self) -> None:
        """
        Initialize database by creating all tables.
        
        Raises:
            DatabaseConnectionError: If database initialization fails
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseConnectionError(f"Failed to initialize database: {e}") from e
            
    def drop_database(self) -> None:
        """
        Drop all database tables.
        
        Warning: This will delete all data!
        
        Raises:
            DatabaseConnectionError: If database drop fails
        """
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise DatabaseConnectionError(f