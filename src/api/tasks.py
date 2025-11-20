"""
Task Management API Endpoints

Provides CRUD operations for task management with user authentication and filtering.
Handles task creation, retrieval, updates, and deletion with proper authorization.

Component ID: COMP-003
Semantic Unit: SU-003

Author: ASP Code Agent
"""

from datetime import datetime
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.models.task import Task, TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority
from src.models.user import User
from src.utils.jwt_utils import get_current_user
from src.database.connection import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router for task endpoints
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TaskResponse:
    """
    Create a new task for the authenticated user.

    Args:
        task_data: Task creation data including title, description, priority, due_date
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        TaskResponse: Created task with generated ID and timestamps

    Raises:
        HTTPException: 400 if validation fails, 500 if database error occurs

    Example:
        POST /tasks
        {
            "title": "Complete project",
            "description": "Finish the task management API",
            "priority": "high",
            "due_date": "2024-12-31T23:59:59Z"
        }
    """
    try:
        # Validate task data
        if not task_data.title or len(task_data.title.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task title cannot be empty"
            )

        if task_data.title and len(task_data.title) > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task title cannot exceed 200 characters"
            )

        if task_data.description and len(task_data.description) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task description cannot exceed 1000 characters"
            )

        # Validate due date is in the future
        if task_data.due_date and task_data.due_date <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date must be in the future"
            )

        # Create new task
        db_task = Task(
            title=task_data.title.strip(),
            description=task_data.description.strip() if task_data.description else None,
            priority=task_data.priority or TaskPriority.MEDIUM,
            due_date=task_data.due_date,
            status=TaskStatus.PENDING,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        logger.info(f"Task created successfully: ID={db_task.id}, User={current_user.id}")
        return TaskResponse.from_orm(db_task)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating task: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task due to database error"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating task: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the task"
        )


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    status_filter: Optional[TaskStatus] = Query(None, description="Filter tasks by status"),
    priority_filter: Optional[TaskPriority] = Query(None, description="Filter tasks by priority"),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[TaskResponse]:
    """
    Retrieve tasks for the authenticated user with optional filtering and pagination.

    Args:
        status_filter: Optional status filter (pending, in_progress, completed, cancelled)
        priority_filter: Optional priority filter (low, medium, high, urgent)
        skip: Number of tasks to skip for pagination
        limit: Maximum number of tasks to return
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        List[TaskResponse]: List of user's tasks matching the filters

    Raises:
        HTTPException: 500 if database error occurs

    Example:
        GET /tasks?status=pending&priority=high&skip=0&limit=10
    """
    try:
        # Build query for user's tasks
        query = db.query(Task).filter(Task.user_id == current_user.id)

        # Apply status filter
        if status_filter:
            query = query.filter(Task.status == status_filter)

        # Apply priority filter
        if priority_filter:
            query = query.filter(Task.priority == priority_filter)

        # Apply ordering (most recent first)
        query = query.order_by(Task.created_at.desc())

        # Apply pagination
        tasks = query.offset(skip).limit(limit).all()

        logger.info(f"Retrieved {len(tasks)} tasks for user {current_user.id}")
        return [TaskResponse.from_orm(task) for task in tasks]

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks due to database error"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving tasks"
        )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TaskResponse:
    """
    Retrieve a specific task by ID for the authenticated user.

    Args:
        task_id: ID of the task to retrieve
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        TaskResponse: Task details if found and owned by user

    Raises:
        HTTPException: 404 if task not found or not owned by user, 500 if database error

    Example:
        GET /tasks/123
    """
    try:
        # Validate task_id
        if task_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task ID must be a positive integer"
            )

        # Query for task owned by current user
        task = db.query(Task).filter(
            Task.id ==