"""
Task SQLAlchemy model with CRUD operations, status management, and user relationship.

This module defines the Task model with comprehensive CRUD operations, status transitions,
and relationship management with User model.

Component ID: COMP-005
Semantic Unit: SU-005

Author: ASP Code Agent
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.database.connection import Base
from src.models.user import User

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enumeration of task priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """
    Task model representing a user task with status management and CRUD operations.
    
    This model provides comprehensive task management functionality including
    status transitions, priority levels, and user relationships.
    
    Attributes:
        id: Primary key identifier
        title: Task title (required, max 200 chars)
        description: Detailed task description (optional)
        status: Current task status (TaskStatus enum)
        priority: Task priority level (TaskPriority enum)
        user_id: Foreign key to User model
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last modified
        due_date: Optional due date for task completion
        completed_at: Timestamp when task was completed
        is_active: Soft delete flag
        
    Relationships:
        user: Many-to-one relationship with User model
    """
    
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Task details
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
    priority = Column(String(10), nullable=False, default=TaskPriority.MEDIUM.value, index=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="tasks")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Soft delete
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_priority', 'user_id', 'priority'),
        Index('idx_status_due_date', 'status', 'due_date'),
        Index('idx_user_active', 'user_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        """String representation of Task instance."""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', user_id={self.user_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Task instance to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all task attributes
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_active": self.is_active
        }
    
    def update_status(self, new_status: TaskStatus) -> bool:
        """
        Update task status with validation and automatic timestamp management.
        
        Args:
            new_status: New status to set for the task
            
        Returns:
            bool: True if status was updated successfully, False otherwise
            
        Raises:
            ValueError: If status transition is invalid
        """
        if not self._is_valid_status_transition(self.status, new_status.value):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status.value}")
        
        old_status = self.status
        self.status = new_status.value
        self.updated_at = datetime.utcnow()
        
        # Set completion timestamp when task is completed
        if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED.value:
            self.completed_at = datetime.utcnow()
        elif new_status != TaskStatus.COMPLETED and self.completed_at:
            self.completed_at = None
            
        logger.info(f"Task {self.id} status updated from {old_status} to {new_status.value}")
        return True
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed.
        
        Args:
            current_status: Current task status
            new_status: Proposed new status
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        valid_transitions = {
            TaskStatus.PENDING.value: [TaskStatus.IN_PROGRESS.value, TaskStatus.CANCELLED.value],
            TaskStatus.IN_PROGRESS.value: [TaskStatus.COMPLETED.value, TaskStatus.PENDING.value, TaskStatus.CANCELLED.value],
            TaskStatus.COMPLETED.value: [TaskStatus.IN_PROGRESS.value],
            TaskStatus.CANCELLED.value: [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def is_overdue(self) -> bool:
        """
        Check if task is overdue based on due_date.
        
        Returns:
            bool: True if task is overdue, False otherwise
        """
        if not self.due_date or self.status == TaskStatus.COMPLETED.value:
            return False
        return datetime.utcnow() > self.due_date
    
    @classmethod
    def create(cls, db: Session, title: str, user_id: int, description: Optional[str] = None,
               priority: TaskPriority = TaskPriority.MEDIUM, due_date: Optional[datetime] = None) -> "Task":
        """
        Create a new task with validation.
        
        Args:
            db: Database session
            title: Task title (required, max 200 chars)
            user_id: ID of the user who owns the task
            description: Optional task description
            priority: Task priority level
            due_date: Optional due date
            
        Returns:
            Task: Created task instance
            
        Raises:
            ValueError: If validation fails
            SQL