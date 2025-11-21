"""
Task management API endpoints for CRUD operations with authentication middleware and user-specific filtering.

This module provides REST API endpoints for managing tasks including creation, retrieval,
updating, and deletion with proper authentication and user-specific data filtering.

Component ID: COMP-003
Semantic Unit: SU-003

Author: ASP Code Agent
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.models.task import Task, TaskStatus, TaskPriority
from src.models.user import User
from src.utils.jwt_utils import decode_jwt_token, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
security = HTTPBearer()


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    
    @validator('title')
    def validate_title(cls, v: str) -> str:
        """Validate and sanitize task title."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize task description."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is not None and v < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        return v


class TaskUpdateRequest(BaseModel):
    """Request model for updating an existing task."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    
    @validator('title')
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize task title."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty or whitespace only")
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize task description."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v is not None and v < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        return v


class TaskResponse(BaseModel):
    """Response model for task data."""
    
    id: UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response model for task list with pagination metadata."""
    
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


def validate_task_ownership(task: Task, user: User) -> None:
    """
    Validate that the current user owns the specified task.
    
    Args:
        task: Task instance to validate
        user: Current authenticated user
        
    Raises:
        HTTPException: If user doesn't own the task
    """
    if task.user_id != user.id:
        logger.warning(f"User {user.id} attempted to access task {task.id} owned by {task.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tasks"
        )


def get_task_by_id(task_id: UUID, db: Session, user: User) -> Task:
    """
    Retrieve a task by ID and validate ownership.
    
    Args:
        task_id: UUID of the task to retrieve
        db: Database session
        user: Current authenticated user
        
    Returns:
        Task: The requested task
        
    Raises:
        HTTPException: If task not found or access denied
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        
        validate_task_ownership(task, user)
        return task
        
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while retrieving task"
        )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Create a new task for the authenticated user.
    
    Args:
        task_data: Task creation data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        TaskResponse: Created task data
        
    Raises:
        HTTPException: If task creation fails
    """
    try:
        logger.info(f"Creating new task for user {current_user.id}")
        
        # Create new task instance
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=task_data.due_date,
            status=TaskStatus.TODO,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        logger.info(f"Successfully created task {new_task.id} for user {current_user.id}")
        return TaskResponse.from_orm(new_task)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating task: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating task