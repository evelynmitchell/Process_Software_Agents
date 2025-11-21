"""
Task SQLAlchemy model with CRUD operations, status management, and foreign key relationship to users.

This module defines the Task model with comprehensive CRUD operations, status transitions,
and proper relationship management with the User model.

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
    
    This model handles task creation, updates, status transitions, and provides
    comprehensive querying capabilities with proper foreign key relationships.
    """
    
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Task details
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
    priority = Column(String(10), nullable=False, default=TaskPriority.MEDIUM.value, index=True)
    
    # Foreign key relationship
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Soft delete flag
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="tasks")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_user_priority", "user_id", "priority"),
        Index("idx_status_due_date", "status", "due_date"),
        Index("idx_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of the Task model."""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', user_id={self.user_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task instance to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all task fields
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
            "is_deleted": self.is_deleted
        }
    
    def is_overdue(self) -> bool:
        """
        Check if task is overdue based on due_date.
        
        Returns:
            bool: True if task is overdue, False otherwise
        """
        if not self.due_date or self.status == TaskStatus.COMPLETED.value:
            return False
        return datetime.utcnow() > self.due_date
    
    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if task can transition to the specified status.
        
        Args:
            new_status (str): Target status to transition to
            
        Returns:
            bool: True if transition is allowed, False otherwise
        """
        valid_transitions = {
            TaskStatus.PENDING.value: [TaskStatus.IN_PROGRESS.value, TaskStatus.CANCELLED.value],
            TaskStatus.IN_PROGRESS.value: [TaskStatus.COMPLETED.value, TaskStatus.PENDING.value, TaskStatus.CANCELLED.value],
            TaskStatus.COMPLETED.value: [TaskStatus.IN_PROGRESS.value],
            TaskStatus.CANCELLED.value: [TaskStatus.PENDING.value]
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def update_status(self, new_status: str) -> bool:
        """
        Update task status with validation and timestamp management.
        
        Args:
            new_status (str): New status to set
            
        Returns:
            bool: True if status was updated successfully, False otherwise
            
        Raises:
            ValueError: If status transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Set completion timestamp
        if new_status == TaskStatus.COMPLETED.value:
            self.completed_at = datetime.utcnow()
        elif old_status == TaskStatus.COMPLETED.value:
            self.completed_at = None
            
        logger.info(f"Task {self.id} status updated from {old_status} to {new_status}")
        return True


class TaskCRUD:
    """
    CRUD operations for Task model with comprehensive querying and management capabilities.
    """
    
    @staticmethod
    def create(
        db: Session,
        title: str,
        user_id: int,
        description: Optional[str] = None,
        priority: str = TaskPriority.MEDIUM.value,
        due_date: Optional[datetime] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            db (Session): Database session
            title (str): Task title (max 200 characters)
            user_id (int): ID of the user who owns the task
            description (Optional[str]): Task description
            priority (str): Task priority level
            due_date (Optional[datetime]): Task due date
            
        Returns:
            Task: Created task instance
            
        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database operation fails
        """
        # Validate inputs
        if not title or len(title.strip()) == 0:
            raise ValueError("Task title cannot be empty")
        
        if len(title) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        
        if priority not in [p.value for p in TaskPriority]:
            raise ValueError(f"Invalid priority: {priority}")
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).