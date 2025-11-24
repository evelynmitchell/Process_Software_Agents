"""
Unit tests for Task model including CRUD operations, status transitions, and user relationships.

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


class TestTaskModel:
    """Test suite for Task model basic functionality."""

    def test_task_creation_with_required_fields(self, db_session: Session, sample_user: User):
        """Test that Task can be created with only required fields."""
        task = Task(
            title="Test Task",
            user_id=sample_user.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.user_id == sample_user.id
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.description is None
        assert task.due_date is None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_creation_with_all_fields(self, db_session: Session, sample_user: User):
        """Test that Task can be created with all fields specified."""
        due_date = datetime.utcnow() + timedelta(days=7)
        task = Task(
            title="Complete Task",
            description="This is a test task with all fields",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=due_date,
            user_id=sample_user.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.title == "Complete Task"
        assert task.description == "This is a test task with all fields"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.due_date == due_date
        assert task.user_id == sample_user.id

    def test_task_creation_without_title_raises_error(self, db_session: Session, sample_user: User):
        """Test that creating Task without title raises IntegrityError."""
        task = Task(user_id=sample_user.id)
        db_session.add(task)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_creation_without_user_id_raises_error(self, db_session: Session):
        """Test that creating Task without user_id raises IntegrityError."""
        task = Task(title="Test Task")
        db_session.add(task)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_creation_with_invalid_user_id_raises_error(self, db_session: Session):
        """Test that creating Task with non-existent user_id raises IntegrityError."""
        task = Task(title="Test Task", user_id=99999)
        db_session.add(task)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_title_max_length_validation(self, db_session: Session, sample_user: User):
        """Test that Task title respects maximum length constraint."""
        long_title = "x" * 201  # Assuming max length is 200
        task = Task(title=long_title, user_id=sample_user.id)
        db_session.add(task)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_description_can_be_long(self, db_session: Session, sample_user: User):
        """Test that Task description can handle long text."""
        long_description = "This is a very long description. " * 100
        task = Task(
            title="Test Task",
            description=long_description,
            user_id=sample_user.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.description == long_description

    def test_task_timestamps_auto_generated(self, db_session: Session, sample_user: User):
        """Test that created_at and updated_at are automatically set."""
        before_creation = datetime.utcnow()
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        after_creation = datetime.utcnow()
        
        assert before_creation <= task.created_at <= after_creation
        assert before_creation <= task.updated_at <= after_creation
        assert task.created_at == task.updated_at

    def test_task_updated_at_changes_on_modification(self, db_session: Session, sample_user: User):
        """Test that updated_at changes when task is modified."""
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        original_updated_at = task.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        task.title = "Updated Task"
        db_session.commit()
        
        assert task.updated_at > original_updated_at


class TestTaskStatusTransitions:
    """Test suite for Task status transitions and validation."""

    def test_task_default_status_is_pending(self, db_session: Session, sample_user: User):
        """Test that new tasks have PENDING status by default."""
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        
        assert task.status == TaskStatus.PENDING

    def test_task_status_can_be_set_to_in_progress(self, db_session: Session, sample_user: User):
        """Test that task status can be changed to IN_PROGRESS."""
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        
        task.status = TaskStatus.IN_PROGRESS
        db_session.commit()
        
        assert task.status == TaskStatus.IN_PROGRESS

    def test_task_status_can_be_set_to_completed(self, db_session: Session, sample_user: User):
        """Test that task status can be changed to COMPLETED."""
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        
        task.status = TaskStatus.COMPLETED
        db_session.commit()
        
        assert task.status == TaskStatus.COMPLETED

    def test_task_status_can_be_set_to_cancelled(self, db_session: Session, sample_user: User):
        """Test that task status can be changed to CANCELLED."""
        task = Task(title="Test Task", user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        
        task.status = TaskStatus.CANCELLED
        db_session.commit()
        
        assert task.status == TaskStatus.CANCELLED

    def test_task_status_transition_from_pending_to_in_progress(self, db_session: Session, sample_user: User):
        """Test valid status transition from PENDING to IN_PROGRESS."""
        task = Task(title="Test Task", user_id=sample_user.id, status=TaskStatus.PENDING)
        db_session.add(task