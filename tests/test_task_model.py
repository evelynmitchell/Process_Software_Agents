"""
Unit tests for Task model

Tests task model validation, status transitions, user relationships, and database operations.

Component ID: COMP-005
Semantic Unit: SU-005

Author: ASP Code Agent
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from src.models.task import Task, TaskStatus, TaskPriority, TaskCreate, TaskUpdate


class TestTaskModel:
    """Test suite for Task model class."""

    def test_task_model_creation_with_valid_data(self):
        """Test that Task model can be created with valid data."""
        task_data = {
            "title": "Test Task",
            "description": "Test description",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.MEDIUM,
            "user_id": 1
        }
        task = Task(**task_data)
        
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.user_id == 1
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_model_creation_with_minimal_data(self):
        """Test that Task model can be created with minimal required data."""
        task_data = {
            "title": "Minimal Task",
            "user_id": 1
        }
        task = Task(**task_data)
        
        assert task.title == "Minimal Task"
        assert task.description is None
        assert task.status == TaskStatus.TODO  # Default value
        assert task.priority == TaskPriority.MEDIUM  # Default value
        assert task.user_id == 1
        assert task.due_date is None
        assert task.completed_at is None

    def test_task_model_creation_with_due_date(self):
        """Test that Task model can be created with due date."""
        due_date = datetime.utcnow() + timedelta(days=7)
        task_data = {
            "title": "Task with Due Date",
            "user_id": 1,
            "due_date": due_date
        }
        task = Task(**task_data)
        
        assert task.due_date == due_date

    def test_task_model_string_representation(self):
        """Test that Task model has proper string representation."""
        task = Task(title="Test Task", user_id=1)
        
        assert str(task) == "Test Task"
        assert repr(task) == f"<Task(id=None, title='Test Task', status=TaskStatus.TODO)>"

    def test_task_model_with_id_representation(self):
        """Test that Task model string representation includes ID when available."""
        task = Task(id=123, title="Test Task", user_id=1)
        
        assert repr(task) == f"<Task(id=123, title='Test Task', status=TaskStatus.TODO)>"


class TestTaskValidation:
    """Test suite for Task model validation."""

    def test_task_title_required(self):
        """Test that task title is required."""
        with pytest.raises(ValidationError) as exc_info:
            Task(user_id=1)
        
        assert "title" in str(exc_info.value)

    def test_task_title_not_empty(self):
        """Test that task title cannot be empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="", user_id=1)
        
        assert "title" in str(exc_info.value)

    def test_task_title_not_whitespace_only(self):
        """Test that task title cannot be whitespace only."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="   ", user_id=1)
        
        assert "title" in str(exc_info.value)

    def test_task_title_max_length(self):
        """Test that task title has maximum length limit."""
        long_title = "x" * 201  # Assuming 200 char limit
        with pytest.raises(ValidationError) as exc_info:
            Task(title=long_title, user_id=1)
        
        assert "title" in str(exc_info.value)

    def test_task_description_max_length(self):
        """Test that task description has maximum length limit."""
        long_description = "x" * 1001  # Assuming 1000 char limit
        with pytest.raises(ValidationError) as exc_info:
            Task(title="Test", description=long_description, user_id=1)
        
        assert "description" in str(exc_info.value)

    def test_task_user_id_required(self):
        """Test that user_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="Test Task")
        
        assert "user_id" in str(exc_info.value)

    def test_task_user_id_positive(self):
        """Test that user_id must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="Test Task", user_id=0)
        
        assert "user_id" in str(exc_info.value)

    def test_task_user_id_negative(self):
        """Test that user_id cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="Test Task", user_id=-1)
        
        assert "user_id" in str(exc_info.value)

    def test_task_due_date_future_validation(self):
        """Test that due date can be in the future."""
        future_date = datetime.utcnow() + timedelta(days=1)
        task = Task(title="Test Task", user_id=1, due_date=future_date)
        
        assert task.due_date == future_date

    def test_task_due_date_past_validation(self):
        """Test that due date can be in the past (for flexibility)."""
        past_date = datetime.utcnow() - timedelta(days=1)
        task = Task(title="Test Task", user_id=1, due_date=past_date)
        
        assert task.due_date == past_date


class TestTaskStatus:
    """Test suite for TaskStatus enum and status transitions."""

    def test_task_status_enum_values(self):
        """Test that TaskStatus enum has expected values."""
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_default_status(self):
        """Test that task has default status of TODO."""
        task = Task(title="Test Task", user_id=1)
        
        assert task.status == TaskStatus.TODO

    def test_task_status_transition_todo_to_in_progress(self):
        """Test valid status transition from TODO to IN_PROGRESS."""
        task = Task(title="Test Task", user_id=1, status=TaskStatus.TODO)
        task.status = TaskStatus.IN_PROGRESS
        
        assert task.status == TaskStatus.IN_PROGRESS

    def test_task_status_transition_in_progress_to_completed(self):
        """Test valid status transition from IN_PROGRESS to COMPLETED."""
        task = Task(title="Test Task", user_id=1, status=TaskStatus.IN_PROGRESS)
        task.status = TaskStatus.COMPLETED
        
        assert task.status == TaskStatus.COMPLETED

    def test_task_status_transition_any_to_cancelled(self):
        """Test that task can be cancelled from any status."""
        task = Task(title="Test Task", user_id=1, status=TaskStatus.TODO)
        task.status = TaskStatus.CANCELLED
        assert