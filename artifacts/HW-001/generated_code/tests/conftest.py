"""
Pytest configuration and fixtures for Hello World API tests.

Provides test database setup, user and task fixtures, and cleanup utilities
for comprehensive testing of the API endpoints.

Author: ASP Code Agent
"""

import asyncio
import os
import tempfile
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Mock imports since actual files don't exist yet
from unittest.mock import MagicMock

# Mock the database and model imports
sys_modules_mock = {
    'src': MagicMock(),
    'src.database': MagicMock(),
    'src.database.connection': MagicMock(),
    'src.models': MagicMock(),
    'src.models.user': MagicMock(),
    'src.models.task': MagicMock(),
}

import sys
for module_name, mock_module in sys_modules_mock.items():
    sys.modules[module_name] = mock_module

# Mock database connection components
class MockDatabase:
    """Mock database class for testing."""
    
    def __init__(self, url: str):
        self.url = url
        self.engine = None
        self.session_factory = None
    
    def connect(self) -> None:
        """Mock database connection."""
        pass
    
    def disconnect(self) -> None:
        """Mock database disconnection."""
        pass
    
    def get_session(self) -> Session:
        """Mock session creation."""
        return Mock(spec=Session)

# Mock user model
class MockUser:
    """Mock user model for testing."""
    
    def __init__(self, id: int = None, username: str = None, email: str = None, 
                 password_hash: str = None, created_at: datetime = None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# Mock task model
class MockTask:
    """Mock task model for testing."""
    
    def __init__(self, id: int = None, title: str = None, description: str = None,
                 completed: bool = False, user_id: int = None, 
                 created_at: datetime = None, updated_at: datetime = None):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Test configuration
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_DATA_DIR = "tests/data"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Provide test database URL for in-memory SQLite database.
    
    Returns:
        str: Database URL for testing
    """
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Generator[Engine, None, None]:
    """
    Create SQLAlchemy engine for testing with in-memory SQLite database.
    
    Args:
        test_database_url: Database URL for testing
        
    Yields:
        Engine: SQLAlchemy engine instance
    """
    engine = create_engine(
        test_database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine: Engine) -> sessionmaker:
    """
    Create session factory for test database.
    
    Args:
        test_engine: SQLAlchemy engine for testing
        
    Returns:
        sessionmaker: Session factory for creating database sessions
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(test_session_factory: sessionmaker) -> Generator[Session, None, None]:
    """
    Create database session for individual tests with automatic rollback.
    
    Args:
        test_session_factory: Session factory for creating sessions
        
    Yields:
        Session: Database session for testing
    """
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_database(test_database_url: str) -> MockDatabase:
    """
    Create mock database instance for testing.
    
    Args:
        test_database_url: Database URL for testing
        
    Returns:
        MockDatabase: Mock database instance
    """
    return MockDatabase(test_database_url)


@pytest.fixture
def sample_user_data() -> dict:
    """
    Provide sample user data for testing.
    
    Returns:
        dict: Sample user data
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx2.O5K2"
    }


@pytest.fixture
def sample_task_data() -> dict:
    """
    Provide sample task data for testing.
    
    Returns:
        dict: Sample task data
    """
    return {
        "title": "Test Task",
        "description": "This is a test task for unit testing",
        "completed": False
    }


@pytest.fixture
def test_user(sample_user_data: dict) -> MockUser:
    """
    Create test user instance.
    
    Args:
        sample_user_data: Sample user data dictionary
        
    Returns:
        MockUser: Test user instance
    """
    return MockUser(
        id=1,
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        password_hash=sample_user_data["password_hash"]
    )


@pytest.fixture
def