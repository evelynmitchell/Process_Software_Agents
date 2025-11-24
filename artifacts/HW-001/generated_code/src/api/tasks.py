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
    TaskStatus
)
from src.utils.jwt_utils import decode_jwt_token, get_current_user
from src.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
security = HTTPBearer()


class TaskService:
    """Service class for task-related business logic."""
    
    def __init__(self, db: Session):
        """
        Initialize TaskService with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_task(self, task_data: TaskCreate, user_id: UUID) -> Task:
        """
        Create a new task for the authenticated user.
        
        Args:
            task_data: Task creation data
            user_id: ID of the user creating the task
            
        Returns:
            Task: Created task instance
            
        Raises:
            HTTPException: If task creation fails
        """
        try:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                status=task_data.status or TaskStatus.PENDING,
                priority=task_data.priority,
                due_date=task_data.due_date,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Task created successfully: {task.id} for user: {user_id}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create task for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )
    
    def get_task_by_id(self, task_id: UUID, user_id: UUID) -> Task:
        """
        Retrieve a task by ID for the authenticated user.
        
        Args:
            task_id: ID of the task to retrieve
            user_id: ID of the authenticated user
            
        Returns:
            Task: Retrieved task instance
            
        Raises:
            HTTPException: If task not found or access denied
        """
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id,
            Task.deleted_at.is_(None)
        ).first()
        
        if not task:
            logger.warning(f"Task not found or access denied: {task_id} for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
    
    def get_user_tasks(
        self,
        user_id: UUID,
        status_filter: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Retrieve tasks for the authenticated user with optional filtering.
        
        Args:
            user_id: ID of the authenticated user
            status_filter: Optional status filter
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List[Task]: List of user's tasks
        """
        query = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.deleted_at.is_(None)
        )
        
        if status_filter:
            query = query.filter(Task.status == status_filter)
        
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(tasks)} tasks for user: {user_id}")
        return tasks
    
    def update_task(self, task_id: UUID, task_data: TaskUpdate, user_id: UUID) -> Task:
        """
        Update an existing task for the authenticated user.
        
        Args:
            task_id: ID of the task to update
            task_data: Task update data
            user_id: ID of the authenticated user
            
        Returns:
            Task: Updated task instance
            
        Raises:
            HTTPException: If task not found or update fails
        """
        task = self.get_task_by_id(task_id, user_id)
        
        try:
            # Update only provided fields
            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)
            
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Task updated successfully: {task_id} for user: {user_id}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update task {task_id} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task"
            )
    
    def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        """
        Soft delete a task for the authenticated user.
        
        Args:
            task_id: ID of the task to delete
            user_id: ID of the authenticated user
            
        Raises:
            HTTPException: If task not found or deletion fails
        """
        task = self.get_task_by_id(task_id, user_id)
        
        try:
            task.deleted_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Task deleted successfully: {task_id} for user: {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete task {task_id} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task"
            )


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """
    Dependency to get TaskService instance.
    
    Args:
        db: Database session dependency
        
    Returns:
        TaskService: Task service instance
    """
    return TaskService(db)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Create a new task for the authenticated user.
    
    Args:
        task_data: Task creation data
        current_