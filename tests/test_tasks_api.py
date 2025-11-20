"""
Integration tests for task CRUD operations API

Tests all task endpoints including authentication, filtering, and authorization scenarios.
Covers CRUD operations, user permissions, and edge cases.

Component ID: COMP-003
Semantic Unit: SU-003

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import json

from src.api.tasks import app
from src.models.task import Task, TaskStatus, TaskPriority
from src.models.user import User
from src.auth.jwt_handler import create_access_token


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True
    )


@pytest.fixture
def mock_admin_user():
    """Create mock admin user for testing."""
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        hashed_password="$2b$12$admin_hash",
        is_active=True,
        is_admin=True
    )


@pytest.fixture
def auth_token(mock_user):
    """Create valid JWT token for testing."""
    return create_access_token(data={"sub": str(mock_user.id)})


@pytest.fixture
def admin_token(mock_admin_user):
    """Create valid admin JWT token for testing."""
    return create_access_token(data={"sub": str(mock_admin_user.id)})


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers with valid token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_task():
    """Create sample task for testing."""
    return Task(
        id=1,
        title="Test Task",
        description="Test task description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        user_id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_task_data():
    """Create sample task data for POST requests."""
    return {
        "title": "New Task",
        "description": "New task description",
        "priority": "high",
        "due_date": "2024-12-31T23:59:59Z"
    }


class TestCreateTask:
    """Test cases for POST /tasks endpoint."""

    @patch('src.api.tasks.create_task')
    @patch('src.api.tasks.get_current_user')
    def test_create_task_success(self, mock_get_user, mock_create, client, mock_user, auth_headers, sample_task_data):
        """Test successful task creation with valid data."""
        mock_get_user.return_value = mock_user
        created_task = Task(id=1, user_id=mock_user.id, **sample_task_data)
        mock_create.return_value = created_task

        response = client.post("/tasks", json=sample_task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["user_id"] == mock_user.id
        mock_create.assert_called_once()

    def test_create_task_unauthorized(self, client, sample_task_data):
        """Test task creation without authentication token."""
        response = client.post("/tasks", json=sample_task_data)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_create_task_invalid_token(self, client, sample_task_data):
        """Test task creation with invalid authentication token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/tasks", json=sample_task_data, headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid token" in data["detail"]

    def test_create_task_missing_title(self, client, auth_headers):
        """Test task creation with missing required title field."""
        task_data = {
            "description": "Task without title",
            "priority": "medium"
        }

        response = client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data["detail"])

    def test_create_task_empty_title(self, client, auth_headers):
        """Test task creation with empty title."""
        task_data = {
            "title": "",
            "description": "Task with empty title",
            "priority": "medium"
        }

        response = client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data["detail"])

    def test_create_task_invalid_priority(self, client, auth_headers):
        """Test task creation with invalid priority value."""
        task_data = {
            "title": "Test Task",
            "description": "Task with invalid priority",
            "priority": "invalid_priority"
        }

        response = client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert "priority" in str(data["detail"])

    def test_create_task_invalid_due_date(self, client, auth_headers):
        """Test task creation with invalid due date format."""
        task_data = {
            "title": "Test Task",
            "description": "Task with invalid due date",
            "priority": "medium",
            "due_date": "invalid_date"
        }

        response = client.post("/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert "due_date" in str(data["detail"])

    @patch('src.api.tasks.create_task')
    @patch('src.api.tasks.get_current_user')
    def test_create_task_database_error(self, mock_get_user, mock_create, client, mock_user, auth_headers, sample_task_data):
        """Test task creation with database error."""
        mock_get_user.return_value = mock_user
        mock_create.side_effect = Exception("Database connection failed")

        response = client.post("/tasks", json=sample_task_data, headers=auth_headers)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestGetTasks:
    """Test cases for GET /tasks endpoint."""

    @patch('src.api.tasks.get_tasks_by_user')
    @patch('src.api.tasks.get_current_user')
    def test_get_tasks_success(self, mock_get_user, mock_get_tasks, client, mock_user, auth_headers, sample_task):
        """Test successful retrieval of user tasks."""
        mock_get_user.return_value = mock_user
        mock_get_tasks.return_value = [sample_task]

        response = client.get("/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data