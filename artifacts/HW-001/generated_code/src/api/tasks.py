"""
Task management API endpoints for CRUD operations with authentication middleware and user authorization.

This module provides REST API endpoints for managing tasks including creation, retrieval,
updating, and deletion with proper user authentication and authorization.

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
from sqlalchemy.orm import Session

from src.models.task import Task
from src.models.user import User
from src.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskListResponse,
    TaskStatus,
    TaskPriority
)
from src.utils.jwt_utils import decode_jwt_token, get_current_user
from src.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
security = HTTPBearer()


def validate_task_ownership(task: Task, current_user: User) -> None:
    """
    Validate that the current user owns the specified task.
    
    Args:
        task: Task instance to validate ownership for
        current_user: Currently authenticated user
        
    Raises:
        HTTPException: If user doesn't own the task (403 Forbidden)
    """
    if task.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to access task {task.id} "
            f"owned by user {task.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this task"
        )


def validate_task_data(task_data: TaskCreate) -> None:
    """
    Validate task creation data for business rules.
    
    Args:
        task_data: Task creation data to validate
        
    Raises:
        HTTPException: If validation fails (400 Bad Request)
    """
    if not task_data.title or not task_data.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot be empty"
        )
    
    if len(task_data.title.strip()) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot exceed 200 characters"
        )
    
    if task_data.description and len(task_data.description) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task description cannot exceed 2000 characters"
        )
    
    if task_data.due_date and task_data.due_date < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be in the past"
        )


def sanitize_task_input(task_data: TaskCreate) -> TaskCreate:
    """
    Sanitize and clean task input data.
    
    Args:
        task_data: Raw task creation data
        
    Returns:
        TaskCreate: Sanitized task data
    """
    # Strip whitespace from title and description
    title = task_data.title.strip() if task_data.title else ""
    description = task_data.description.strip() if task_data.description else None
    
    return TaskCreate(
        title=title,
        description=description,
        status=task_data.status or TaskStatus.TODO,
        priority=task_data.priority or TaskPriority.MEDIUM,
        due_date=task_data.due_date,
        tags=task_data.tags or []
    )


def build_task_filters(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    tag: Optional[str] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None
) -> dict:
    """
    Build filter dictionary for task queries.
    
    Args:
        status: Filter by task status
        priority: Filter by task priority
        tag: Filter by tag (partial match)
        due_before: Filter tasks due before this date
        due_after: Filter tasks due after this date
        
    Returns:
        dict: Filter conditions for database query
    """
    filters = {}
    
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    if tag:
        filters['tag'] = tag
    if due_before:
        filters['due_before'] = due_before
    if due_after:
        filters['due_after'] = due_after
        
    return filters


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Create a new task for the authenticated user.
    
    Args:
        task_data: Task creation data
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        TaskResponse: Created task data
        
    Raises:
        HTTPException: If validation fails or creation error occurs
    """
    try:
        # Validate and sanitize input
        validate_task_data(task_data)
        sanitized_data = sanitize_task_input(task_data)
        
        # Create new task
        new_task = Task(
            title=sanitized_data.title,
            description=sanitized_data.description,
            status=sanitized_data.status,
            priority=sanitized_data.priority,
            due_date=sanitized_data.due_date,
            tags=sanitized_data.tags,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        logger.info(f"Task {new_task.id} created by user {current_user.id}")
        
        return TaskResponse.from_orm(new_task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task for user {current_user.id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/", response_model=TaskListResponse)
def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority_filter: Optional[TaskPriority] = Query(None, alias="priority"),
    tag_filter: Optional[str] = Query(None, alias="tag", max_length=50),
    due_before: Optional[datetime] = Query(None),
    due_after: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, max_length=200, description="Search in title and description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskListResponse:
    """
    Retrieve tasks for the authenticated user with filtering and pagination.
    
    Args:
        skip: Number of tasks to skip for pagination
        limit: Maximum number of tasks to return
        status_filter: Filter by task status
        priority_filter: