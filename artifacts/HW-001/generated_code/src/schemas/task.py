"""
Pydantic schemas for task management API

Defines data models for task creation, updates, filtering, and API responses
with comprehensive validation rules.

Component ID: COMP-007
Semantic Unit: SU-007

Author: ASP Code Agent
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator


class TaskStatus(str, Enum):
    """Enumeration of valid task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enumeration of valid task priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskBase(BaseModel):
    """Base schema with common task fields."""
    
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
    tags: List[str] = Field(
        default_factory=list,
        description="List of task tags"
    )

    @validator('title')
    def validate_title(cls, v: str) -> str:
        """Validate and clean task title."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        
        # Remove extra whitespace and normalize
        cleaned_title = ' '.join(v.strip().split())
        
        if len(cleaned_title) < 1:
            raise ValueError('Title must contain at least one non-whitespace character')
        
        return cleaned_title

    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task description."""
        if v is None:
            return None
        
        # Remove extra whitespace but preserve line breaks
        cleaned_desc = v.strip()
        
        if not cleaned_desc:
            return None
        
        return cleaned_desc

    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is None:
            return None
        
        if v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        
        return v

    @validator('tags')
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean task tags."""
        if not v:
            return []
        
        # Remove duplicates and empty tags, normalize case
        cleaned_tags = []
        seen_tags = set()
        
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            cleaned_tag = tag.strip().lower()
            
            if not cleaned_tag:
                continue  # Skip empty tags
            
            if len(cleaned_tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
            
            if not cleaned_tag.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Tags can only contain alphanumeric characters, hyphens, and underscores')
            
            if cleaned_tag not in seen_tags:
                cleaned_tags.append(cleaned_tag)
                seen_tags.add(cleaned_tag)
        
        if len(cleaned_tags) > 10:
            raise ValueError('Cannot have more than 10 tags per task')
        
        return cleaned_tags


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    
    assigned_to: Optional[UUID] = Field(
        None,
        description="UUID of user assigned to this task"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the new API endpoints",
                "priority": "high",
                "due_date": "2024-12-31T23:59:59Z",
                "tags": ["documentation", "api", "urgent"],
                "assigned_to": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class TaskUpdate(BaseModel):
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
        description="Updated due date"
    )
    assigned_to: Optional[UUID] = Field(
        None,
        description="Updated assigned user UUID"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Updated list of tags"
    )

    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task title."""
        if v is None:
            return None
        
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        
        cleaned_title = ' '.join(v.strip().split())
        
        if len(cleaned_title) < 1:
            raise ValueError('Title must contain at least one non-whitespace character')
        
        return cleaned_title

    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task description."""
        if v is None:
            return None
        
        cleaned_desc = v.strip()
        
        if not cleaned_desc:
            return None
        
        return cleaned_desc

    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is None:
            return None
        
        if v < datetime.utcnow():
            raise ValueError('Due date cannot be in the past')
        
        return v

    @validator('tags')
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean task tags."""
        if v is None:
            return None
        
        # Use same validation logic as TaskBase
        cleaned_tags = []
        seen_tags = set()
        
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            cleaned_tag = tag.strip().lower()
            
            if not cleaned_tag:
                continue
            
            if len(cleaned_tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
            
            if not cleaned_tag.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Tags can only contain alphanumeric characters, hyphens, and underscores')
            
            if cleaned_tag not in seen_tags:
                cleaned_tags.append(cleaned_tag)
                seen_tags.add(cleaned_tag)
        
        if len(cleaned_tags) > 10:
            raise ValueError('Cannot have more than 10