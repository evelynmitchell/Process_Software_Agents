"""
Pydantic schemas for task request/response validation.

This module defines the data models used for task-related API endpoints,
including create, update, and response schemas with proper validation.

Component ID: COMP-007
Semantic Unit: SU-007

Author: ASP Code Agent
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enumeration of task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreateRequest(BaseModel):
    """Schema for creating a new task."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed task description"
    )
    priority: TaskPriority = Field(
        TaskPriority.MEDIUM,
        description="Task priority level"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Task due date and time"
    )
    tags: Optional[list[str]] = Field(
        None,
        description="List of task tags"
    )
    
    @validator('title')
    def validate_title(cls, v: str) -> str:
        """Validate task title is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task description."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is not None and v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v
    
    @validator('tags')
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate and clean task tags."""
        if v is not None:
            # Remove empty tags and duplicates while preserving order
            cleaned_tags = []
            seen = set()
            for tag in v:
                tag = tag.strip().lower()
                if tag and tag not in seen:
                    if len(tag) > 50:
                        raise ValueError('Tag length cannot exceed 50 characters')
                    cleaned_tags.append(tag)
                    seen.add(tag)
            return cleaned_tags if cleaned_tags else None
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class TaskUpdateRequest(BaseModel):
    """Schema for updating an existing task."""
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Updated task title"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated task description"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Updated task status"
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="Updated task priority"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Updated task due date"
    )
    tags: Optional[list[str]] = Field(
        None,
        description="Updated list of task tags"
    )
    
    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate task title is not empty after stripping whitespace."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Title cannot be empty or only whitespace')
        return v
    
    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task description."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is not None and v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        return v
    
    @validator('tags')
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate and clean task tags."""
        if v is not None:
            # Remove empty tags and duplicates while preserving order
            cleaned_tags = []
            seen = set()
            for tag in v:
                tag = tag.strip().lower()
                if tag and tag not in seen:
                    if len(tag) > 50:
                        raise ValueError('Tag length cannot exceed 50 characters')
                    cleaned_tags.append(tag)
                    seen.add(tag)
            return cleaned_tags if cleaned_tags else None
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class TaskResponse(BaseModel):
    """Schema for task response data."""
    
    id: UUID = Field(
        ...,
        description="Unique task identifier"
    )
    title: str = Field(
        ...,
        description="Task title"
    )
    description: Optional[str] = Field(
        None,
        description="Task description"
    )
    status: TaskStatus = Field(
        ...,
        description="Current task status"
    )
    priority: TaskPriority = Field(
        ...,
        description="Task priority level"
    )
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Task last update timestamp"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Task due date"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Task completion timestamp"
    )
    tags: Optional[list[str]] = Field(
        None,
        description="List of task tags"
    )

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""
    
    tasks: list[TaskResponse] = Field(
        ...,
        description="List of tasks"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of tasks"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of tasks per page"
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages"