"""
Unit tests for Task model CRUD operations, status transitions, and user relationships.

Tests all Task model functionality including creation, updates, status changes,
and relationships with User model.

Component ID: COMP-005
Semantic Unit: SU-005

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.task import Task, TaskStatus, TaskPriority
from src.models.user import User


@pytest.fixture
def db_session():
    """Mock database session for testing."""
    session = Mock(spec=Session)
    return session


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    return user


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "user_id": 1
    }


@pytest.fixture
def sample_task(sample_user, sample_task_data):
    """Create a sample task for testing."""
    task = Task(**sample_task_data)
    task.id = 1
    task.user = sample_user
    task.created_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    return task


class TestTaskModel:
    """Test Task model basic functionality."""

    def test_task_creation_with_required_fields(self, sample_task_data):
        """Test that task can be created with required fields only."""
        task = Task(
            title=sample_task_data["title"],
            user_id=sample_task_data["user_id"]
        )
        
        assert task.title == sample_task_data["title"]
        assert task.user_id == sample_task_data["user_id"]
        assert task.status == TaskStatus.TODO  # Default status
        assert task.priority == TaskPriority.MEDIUM  # Default priority
        assert task.description is None
        assert task.due_date is None

    def test_task_creation_with_all_fields(self, sample_task_data):
        """Test that task can be created with all fields."""
        due_date = datetime.now(timezone.utc)
        task = Task(
            title=sample_task_data["title"],
            description=sample_task_data["description"],
            status=sample_task_data["status"],
            priority=sample_task_data["priority"],
            user_id=sample_task_data["user_id"],
            due_date=due_date
        )
        
        assert task.title == sample_task_data["title"]
        assert task.description == sample_task_data["description"]
        assert task.status == sample_task_data["status"]
        assert task.priority == sample_task_data["priority"]
        assert task.user_id == sample_task_data["user_id"]
        assert task.due_date == due_date

    def test_task_string_representation(self, sample_task):
        """Test task string representation."""
        expected = f"Task(id={sample_task.id}, title='{sample_task.title}', status={sample_task.status.value})"
        assert str(sample_task) == expected

    def test_task_repr_representation(self, sample_task):
        """Test task repr representation."""
        expected = f"<Task id={sample_task.id} title='{sample_task.title}' user_id={sample_task.user_id}>"
        assert repr(sample_task) == expected


class TestTaskCRUDOperations:
    """Test Task model CRUD operations."""

    def test_create_task_success(self, db_session, sample_task_data):
        """Test successful task creation."""
        task = Task(**sample_task_data)
        
        # Mock successful database operations
        db_session.add.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None
        
        # Simulate database assigning ID and timestamps
        task.id = 1
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        
        result = task.create(db_session)
        
        assert result == task
        assert task.id == 1
        assert task.created_at is not None
        assert task.updated_at is not None
        db_session.add.assert_called_once_with(task)
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(task)

    def test_create_task_database_error(self, db_session, sample_task_data):
        """Test task creation with database error."""
        task = Task(**sample_task_data)
        
        # Mock database error
        db_session.commit.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(IntegrityError):
            task.create(db_session)
        
        db_session.rollback.assert_called_once()

    def test_get_task_by_id_success(self, db_session, sample_task):
        """Test successful task retrieval by ID."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = Task.get_by_id(db_session, sample_task.id)
        
        assert result == sample_task
        db_session.query.assert_called_once_with(Task)

    def test_get_task_by_id_not_found(self, db_session):
        """Test task retrieval by ID when task doesn't exist."""
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = Task.get_by_id(db_session, 999)
        
        assert result is None

    def test_get_tasks_by_user_id(self, db_session, sample_task):
        """Test retrieving tasks by user ID."""
        tasks = [sample_task]
        db_session.query.return_value.filter.return_value.all.return_value = tasks
        
        result = Task.get_by_user_id(db_session, sample_task.user_id)
        
        assert result == tasks
        db_session.query.assert_called_once_with(Task)

    def test_update_task_success(self, db_session, sample_task):
        """Test successful task update."""
        update_data = {
            "title": "Updated Task Title",
            "description": "Updated description",
            "priority": TaskPriority.HIGH
        }
        
        db_session.commit.return_value = None
        db_session.refresh.return_value = None
        
        result = sample_task.update(db_session, **update_data)
        
        assert result == sample_task
        assert sample_task.title == update_data["title"]
        assert sample_task.description == update_data["description"]
        assert sample_task.priority == update_data["priority"]
        assert sample_task.updated_at is not None
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(sample_task)

    def test_update_task_with_invalid_field(self, db_session, sample_task):
        """Test task update with invalid field."""
        original_title = sample_task.title
        
        with pytest.raises(AttributeError):
            sample_task.update(db_session, invalid_field="value")
        
        # Ensure original data is unchanged
        assert sample