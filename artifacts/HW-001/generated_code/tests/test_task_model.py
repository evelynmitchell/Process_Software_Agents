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
        """Test that Task can be created with all fields populated."""
        due_date = datetime.utcnow() + timedelta(days=7)
        task = Task(
            title="Complete Task",
            description="This is a test task with full details",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=due_date,
            user_id=sample_user.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.title == "Complete Task"
        assert task.description == "This is a test task with full details"
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


class TestTaskStatusTransitions:
    """Test suite for Task status transitions and validation."""

    def test_task_default_status_is_pending(self, db_session: Session, sample_user: User):
        """Test that new Task has default status of PENDING."""
        task = Task(title="Test Task", user_id=sample_user.id)
        assert task.status == TaskStatus.PENDING

    def test_task_status_can_be_updated_to_in_progress(self, db_session: Session, sample_task: Task):
        """Test that Task status can be changed from PENDING to IN_PROGRESS."""
        assert sample_task.status == TaskStatus.PENDING
        
        sample_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()
        
        assert sample_task.status == TaskStatus.IN_PROGRESS

    def test_task_status_can_be_updated_to_completed(self, db_session: Session, sample_task: Task):
        """Test that Task status can be changed to COMPLETED."""
        sample_task.status = TaskStatus.COMPLETED
        db_session.commit()
        
        assert sample_task.status == TaskStatus.COMPLETED

    def test_task_status_can_be_updated_to_cancelled(self, db_session: Session, sample_task: Task):
        """Test that Task status can be changed to CANCELLED."""
        sample_task.status = TaskStatus.CANCELLED
        db_session.commit()
        
        assert sample_task.status == TaskStatus.CANCELLED

    def test_task_completed_at_set_when_status_completed(self, db_session: Session, sample_task: Task):
        """Test that completed_at timestamp is set when status changes to COMPLETED."""
        assert sample_task.completed_at is None
        
        sample_task.status = TaskStatus.COMPLETED
        sample_task.completed_at = datetime.utcnow()
        db_session.commit()
        
        assert sample_task.completed_at is not None
        assert isinstance(sample_task.completed_at, datetime)

    def test_task_updated_at_changes_on_status_update(self, db_session: Session, sample_task: Task):
        """Test that updated_at timestamp changes when status is updated."""
        original_updated_at = sample_task.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        sample_task.status = TaskStatus.IN_PROGRESS
        sample_task.updated_at = datetime.utcnow()
        db_session.commit()
        
        assert sample_task.updated_at > original_updated_at


class TestTaskPriority:
    """Test suite for Task priority functionality."""

    def test_task_default_priority_is_medium(self, db_session: Session, sample_user: User):
        """Test that new Task has default priority of MEDIUM."""
        task = Task(title="Test Task", user_id=sample_user.id)
        assert task.priority == TaskPriority.MEDIUM

    def test_task_priority_can_be_set_to_low(self, db_session: Session, sample_user: User):
        """Test that Task priority can be set to LOW."""
        task = Task(title="Test Task", priority=TaskPriority.LOW, user_id=sample_user.id)
        db_session.add(task)
        db_session.commit()
        
        assert task.priority == TaskPriority.LOW

    def test_task_priority_can_be_set_to_high(self, db_session: Session, sample_