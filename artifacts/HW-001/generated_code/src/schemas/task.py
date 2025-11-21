"""
Pydantic schemas for task management API

Defines data models for task creation, updates, filtering, and API responses
with comprehensive validation rules and serialization logic.

Component ID: COMP-007
Semantic Unit: SU-007

Author: ASP Code Agent
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
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
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean task tags."""
        if not v:
            return []
        
        # Remove duplicates and empty tags
        cleaned_tags = []
        seen = set()
        
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            tag = tag.strip().lower()
            if tag and len(tag) <= 50 and tag not in seen:
                if not tag.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f'Tag "{tag}" contains invalid characters')
                cleaned_tags.append(tag)
                seen.add(tag)
        
        if len(cleaned_tags) > 10:
            raise ValueError('Maximum 10 tags allowed per task')
        
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
                "description": "Write comprehensive documentation for the new API",
                "priority": "high",
                "due_date": "2024-12-31T23:59:59Z",
                "tags": ["documentation", "api", "project"],
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
        description="Updated task tags"
    )
    
    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean task title."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Title cannot be empty or whitespace only')
            return v.strip()
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
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean task tags."""
        if v is None:
            return None
        
        # Remove duplicates and empty tags
        cleaned_tags = []
        seen = set()
        
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            tag = tag.strip().lower()
            if tag and len(tag) <= 50 and tag not in seen:
                if not tag.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f'Tag "{tag}" contains invalid characters')
                cleaned_tags.append(tag)
                seen.add(tag)
        
        if len(cleaned_tags) > 10:
            raise ValueError('Maximum 10 tags allowed per task')
        
        return cleaned_tags
    
    @root_validator
    def validate_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure at least one field is provided for update."""
        if not any(v is not None for v in values.values()):
            raise ValueError('At least one field must be provided for update')
        return values
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "in_progress",
                "priority": "urgent",
                "due_date": "2024-12-25T18:00:00Z"
            }
        }


class TaskFilter(BaseModel):
    """Schema for filtering tasks in list queries."""
    
    status: Optional[TaskStatus] = Field(
        None,
        description="Filter by task status"
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="Filter by task priority"
    )
    assigned_to: Optional[UUID] = Field(
        None,
        description="Filter by assigne