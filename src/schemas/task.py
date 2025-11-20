"""
Pydantic schemas for task data validation.

This module defines the data validation schemas for task-related operations
including create, update, and response models with status enums.

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
    FAILED = "failed"


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
            raise ValueError('Title cannot be empty or whitespace only')
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
                    cleaned_tags.append(tag)
                    seen.add(tag)
            return cleaned_tags if cleaned_tags else None
        return v


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
                raise ValueError('Title cannot be empty or whitespace only')
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
                    cleaned_tags.append(tag)
                    seen.add(tag)
            return cleaned_tags if cleaned_tags else None
        return v


class TaskResponse(BaseModel):
    """Schema for task response data."""
    
    id: UUID = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(..., description="Current task status")
    priority: TaskPriority = Field(..., description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    tags: Optional[list[str]] = Field(None, description="Task tags")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(
        None,
        description="Task completion timestamp"
    )
    
    class Config:
        """Pydantic model configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None,
            UUID: str
        }
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the API",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2024-01-15T10:00:00Z",
                "tags": ["documentation", "api", "urgent"],
                "created_at": "2024-01-01T09:00:00Z",
                "updated_at": "2024-01-02T14:30:00Z",
                "completed_at": None
            }
        }


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""
    
    tasks: list[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., ge=0, description="Total number of tasks")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    
    class Config:
        """Pydantic model configuration."""
        
        schema_extra = {
            "example": {
                "tasks": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "