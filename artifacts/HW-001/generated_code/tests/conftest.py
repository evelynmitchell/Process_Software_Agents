"""
Pytest configuration and fixtures for Hello World API tests.

Provides test database setup, user and task fixtures, and cleanup utilities
for comprehensive testing of the API endpoints and business logic.

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

# Import application components
from src.database.connection import Base, get_db_session
from src.models.user import User
from src.models.task import Task


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop for async tests
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """
    Create SQLAlchemy engine for testing with in-memory SQLite database.
    
    Yields:
        Engine: SQLAlchemy engine configured for testing
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
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
def test_session_factory(test_engine: Engine) -> Generator[sessionmaker, None, None]:
    """
    Create session factory for test database.
    
    Args:
        test_engine: SQLAlchemy engine for testing
        
    Yields:
        sessionmaker: Session factory for creating database sessions
    """
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    yield TestSessionLocal


@pytest.fixture(autouse=True)
def setup_test_database(test_engine: Engine) -> Generator[None, None, None]:
    """
    Set up and tear down test database for each test.
    
    Args:
        test_engine: SQLAlchemy engine for testing
        
    Yields:
        None
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after test
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_session_factory: sessionmaker) -> Generator[Session, None, None]:
    """
    Create database session for individual tests.
    
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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with database session override.
    
    Args:
        db_session: Database session for testing
        
    Yields:
        TestClient: FastAPI test client
    """
    from main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict[str, str]:
    """
    Provide sample user data for testing.
    
    Returns:
        dict: Sample user data with valid fields
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }


@pytest.fixture
def sample_task_data() -> dict[str, str]:
    """
    Provide sample task data for testing.
    
    Returns:
        dict: Sample task data with valid fields
    """
    return {
        "title": "Test Task",
        "description": "This is a test task for unit testing",
        "priority": "medium",
        "status": "pending"
    }


@pytest.fixture
def test_user(db_session: Session, sample_user_data: dict[str, str]) -> User:
    """
    Create a test user in the database.
    
    Args:
        db_session: Database session for testing
        sample_user_data: Sample user data
        
    Returns:
        User: Created test user instance
    """
    user = User(
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        hashed_password="$2b$12$hashed_password_placeholder"  # Mock hashed password
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_task(db_session: Session, test_user: User, sample_task_data: dict[str, str]) -> Task:
    """
    Create a test task in the database.
    
    Args:
        db_session: Database session for testing
        test_user: Test user who owns the task
        sample_task_data: Sample task data
        
    Returns:
        Task: Created test task instance
    """
    task = Task(
        title=sample_task_data["title"],
        description=sample_task_data["description"],
        priority=sample_task_data["priority"],
        status=sample_task_data["status"],
        user_id=test_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def multiple_users(db_session: Session) -> list[User]:
    """
    Create multiple test users for testing pagination and filtering.
    
    Args:
        db_session: Database session for testing
        
    Returns:
        list[User]: List of created test users
    """
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            hashed_password="$2b$12$hashed_password_placeholder"
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users


@pytest.fixture
def multiple_tasks(db_session: Session, test_user: User) -> list[Task]:
    """
    Create multiple test tasks for testing pagination and filtering.
    
    Args:
        db_session: Database session for testing
        test_user: Test user who owns the tasks
        
    Returns:
        list[Task]: List of created test tasks
    """