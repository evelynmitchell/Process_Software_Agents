"""
Task database model with SQLAlchemy ORM

Defines the Task model with title, description, status, priority, and user relationship.

Component ID: COMP-005
Semantic Unit: SU-005

Author: ASP Code Generator
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.database.connection import Base


class TaskStatus(str, Enum):
    """Enumeration for task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enumeration for task priority values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """
    Task model representing a user task in the system.
    
    Attributes:
        id: Primary key identifier
        title: Task title (required, max 200 characters)
        description: Detailed task description (optional)
        status: Current task status (default: pending)
        priority: Task priority level (default: medium)
        user_id: Foreign key to user who owns the task
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last modified
        due_date: Optional due date for task completion
        
    Relationships:
        user: User who owns this task
    """
    
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Task details
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Task metadata
    status = Column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True
    )
    priority = Column(
        SQLEnum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    due_date = Column(DateTime, nullable=True, index=True)
    
    # Foreign key relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    
    def __repr__(self) -> str:
        """
        String representation of Task instance.
        
        Returns:
            str: Human-readable representation of the task
        """
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"status='{self.status.value}', priority='{self.priority.value}', "
            f"user_id={self.user_id})>"
        )
    
    def __str__(self) -> str:
        """
        String representation for display purposes.
        
        Returns:
            str: Display-friendly task representation
        """
        return f"Task: {self.title} ({self.status.value})"
    
    def to_dict(self) -> dict:
        """
        Convert task instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all task attributes
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }
    
    def is_overdue(self) -> bool:
        """
        Check if task is overdue based on due_date.
        
        Returns:
            bool: True if task has due_date and it's in the past, False otherwise
        """
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date
    
    def is_completed(self) -> bool:
        """
        Check if task is completed.
        
        Returns:
            bool: True if task status is completed, False otherwise
        """
        return self.status == TaskStatus.COMPLETED
    
    def is_active(self) -> bool:
        """
        Check if task is active (not completed or cancelled).
        
        Returns:
            bool: True if task is pending or in progress, False otherwise
        """
        return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    
    def mark_completed(self) -> None:
        """
        Mark task as completed and update timestamp.
        """
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def mark_in_progress(self) -> None:
        """
        Mark task as in progress and update timestamp.
        """
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self) -> None:
        """
        Mark task as cancelled and update timestamp.
        """
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def update_priority(self, priority: TaskPriority) -> None:
        """
        Update task priority and timestamp.
        
        Args:
            priority: New priority level for the task
            
        Raises:
            ValueError: If priority is not a valid TaskPriority enum value
        """
        if not isinstance(priority, TaskPriority):
            raise ValueError(f"Priority must be a TaskPriority enum value, got {type(priority)}")
        
        self.priority = priority
        self.updated_at = datetime.utcnow()
    
    def set_due_date(self, due_date: Optional[datetime]) -> None:
        """
        Set or update task due date.
        
        Args:
            due_date: New due date for the task, or None to remove due date
            
        Raises:
            ValueError: If due_date is in the past
        """
        if due_date is not None and due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        
        self.due_date = due_date
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_valid_statuses(cls) -> list[str]:
        """
        Get list of valid task status values.
        
        Returns:
            list[str]: List of valid status string values
        """
        return [status.value for status in TaskStatus]
    
    @classmethod
    def get_valid_priorities(cls) -> list[str]:
        """
        Get list of valid task priority values.
        
        Returns:
            list[str]: List of valid priority string values
        """
        return [priority.value for priority in TaskPriority]