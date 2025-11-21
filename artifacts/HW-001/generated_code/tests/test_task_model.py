"""
Unit tests for Task model CRUD operations, status transitions, and user relationships.

Tests all Task model functionality including creation, updates, status changes,
and relationships with User model.

Component ID: COMP-005
Semantic Unit: SU-005

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timedelta
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
def sample_task(sample_user):
    """Create a sample task for testing."""
    task = Task(
        id=1,
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        user_id=sample_user.id,
        user=sample_user,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return task


class TestTaskModel:
    """Test cases for Task model basic functionality."""

    def test_task_creation_with_required_fields(self, sample_user):
        """Test that task can be created with only required fields."""
        task = Task(
            title="New Task",
            description="Task description",
            user_id=sample_user.id
        )
        
        assert task.title == "New Task"
        assert task.description == "Task description"
        assert task.user_id == sample_user.id
        assert task.status == TaskStatus.TODO  # Default status
        assert task.priority == TaskPriority.MEDIUM  # Default priority
        assert task.created_at is None  # Set by database
        assert task.updated_at is None  # Set by database

    def test_task_creation_with_all_fields(self, sample_user):
        """Test that task can be created with all fields specified."""
        now = datetime.utcnow()
        task = Task(
            title="Complete Task",
            description="Detailed description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            user_id=sample_user.id,
            due_date=now + timedelta(days=7),
            created_at=now,
            updated_at=now
        )
        
        assert task.title == "Complete Task"
        assert task.description == "Detailed description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.user_id == sample_user.id
        assert task.due_date == now + timedelta(days=7)
        assert task.created_at == now
        assert task.updated_at == now

    def test_task_string_representation(self, sample_task):
        """Test task string representation."""
        expected = f"<Task(id=1, title='Test Task', status=TaskStatus.TODO)>"
        assert str(sample_task) == expected

    def test_task_repr_representation(self, sample_task):
        """Test task repr representation."""
        expected = f"<Task(id=1, title='Test Task', status=TaskStatus.TODO)>"
        assert repr(sample_task) == expected


class TestTaskCRUDOperations:
    """Test cases for Task CRUD operations."""

    def test_create_task_success(self, db_session, sample_user):
        """Test successful task creation."""
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "user_id": sample_user.id
        }
        
        task = Task.create(db_session, **task_data)
        
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
        assert task.title == "New Task"
        assert task.description == "Task description"
        assert task.user_id == sample_user.id

    def test_create_task_database_error(self, db_session, sample_user):
        """Test task creation with database error."""
        db_session.commit.side_effect = IntegrityError("", "", "")
        
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "user_id": sample_user.id
        }
        
        with pytest.raises(IntegrityError):
            Task.create(db_session, **task_data)
        
        db_session.rollback.assert_called_once()

    def test_get_task_by_id_success(self, db_session, sample_task):
        """Test successful task retrieval by ID."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_task
        
        result = Task.get_by_id(db_session, 1)
        
        assert result == sample_task
        db_session.query.assert_called_once_with(Task)

    def test_get_task_by_id_not_found(self, db_session):
        """Test task retrieval by ID when task doesn't exist."""
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = Task.get_by_id(db_session, 999)
        
        assert result is None

    def test_get_tasks_by_user_id(self, db_session, sample_task, sample_user):
        """Test retrieving all tasks for a specific user."""
        db_session.query.return_value.filter.return_value.all.return_value = [sample_task]
        
        result = Task.get_by_user_id(db_session, sample_user.id)
        
        assert result == [sample_task]
        db_session.query.assert_called_once_with(Task)

    def test_get_tasks_by_user_id_empty(self, db_session):
        """Test retrieving tasks for user with no tasks."""
        db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = Task.get_by_user_id(db_session, 999)
        
        assert result == []

    def test_update_task_success(self, db_session, sample_task):
        """Test successful task update."""
        update_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "priority": TaskPriority.HIGH
        }
        
        updated_task = Task.update(db_session, sample_task, **update_data)
        
        assert updated_task.title == "Updated Task"
        assert updated_task.description == "Updated description"
        assert updated_task.priority == TaskPriority.HIGH
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()

    def test_update_task_database_error(self, db_session, sample_task):
        """Test task update with database error."""
        db_session.commit.side_effect = SQLAlchemyError("Database error")
        
        update_data = {"title": "Updated Task"}
        
        with pytest.raises(SQLAlchemyError):
            Task.update(db_session, sample_task, **update_data)
        
        db_session.rollback.assert_called_once()

    def test_delete_task_success(self, db_session, sample_task):
        """Test successful task deletion."""
        result = Task.delete(db_session, sample