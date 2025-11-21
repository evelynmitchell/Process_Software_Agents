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

from sqlalchemy import create_engine, event, text
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
    """Database configuration management."""
    
    def __init__(self) -> None:
        """Initialize database configuration from environment variables."""
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "sqlite:///./hello_world.db"
        )
        self.echo_sql: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        self.pool_timeout: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.pool_recycle: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    
    def get_engine_kwargs(self) -> dict:
        """
        Get SQLAlchemy engine configuration parameters.
        
        Returns:
            dict: Engine configuration parameters
        """
        kwargs = {
            "echo": self.echo_sql,
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


class DatabaseConnection:
    """Database connection and session management."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None) -> None:
        """
        Initialize database connection.
        
        Args:
            config: Database configuration instance
        """
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    @property
    def engine(self) -> Engine:
        """
        Get SQLAlchemy engine instance.
        
        Returns:
            Engine: SQLAlchemy engine
            
        Raises:
            RuntimeError: If engine is not initialized
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized. Call initialize() first.")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """
        Get SQLAlchemy session factory.
        
        Returns:
            sessionmaker: Session factory instance
            
        Raises:
            RuntimeError: If session factory is not initialized
        """
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized. Call initialize() first.")
        return self._session_factory
    
    def initialize(self) -> None:
        """
        Initialize database engine and session factory.
        
        Raises:
            SQLAlchemyError: If database initialization fails
        """
        try:
            logger.info(f"Initializing database connection to {self.config.database_url}")
            
            # Create engine
            engine_kwargs = self.config.get_engine_kwargs()
            self._engine = create_engine(self.config.database_url, **engine_kwargs)
            
            # Set up event listeners
            self._setup_event_listeners()
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            # Test connection
            self._test_connection()
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise SQLAlchemyError(f"Database initialization failed: {e}") from e
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for connection management."""
        if self._engine is None:
            return
        
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and reliability."""
            if self.config.database_url.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                cursor.close()
        
        @event.listens_for(self._engine, "engine_connect")
        def log_connection(conn, branch):
            """Log database connections."""
            logger.debug("Database connection established")
    
    def _test_connection(self) -> None:
        """
        Test database connection.
        
        Raises:
            SQLAlchemyError: If connection test fails
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.debug("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise SQLAlchemyError(f"Connection test failed: {e}") from e
    
    def create_tables(self) -> None:
        """
        Create all database tables defined in models.
        
        Raises:
            SQLAlchemyError: If table creation fails
        """
        try:
            logger.info("Creating database tables")
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise SQLAlchemyError(f"Table creation failed: {e}") from e
    
    def drop_tables(self) -> None:
        """
        Drop all database tables.
        
        Raises:
            SQLAlchemyError: If table dropping fails
        """
        try:
            logger.warning("Dropping all database tables")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise SQLAlchemyError(f"Table dropping failed: {e}") from e
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy session instance
            
        Raises:
            SQLAlchemyError: If session creation or operation fails
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise SQLAlchemyError(f"Session