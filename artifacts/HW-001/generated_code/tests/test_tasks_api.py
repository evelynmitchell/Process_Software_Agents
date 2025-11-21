"""
Integration tests for task CRUD operations API endpoints.

Tests task creation, retrieval, updating, deletion, filtering, pagination,
and authorization checks for the tasks API.

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


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database connection for testing."""
    with patch('src.api.tasks.get_db') as mock:
        db_mock = Mock()
        mock.return_value = db_mock
        yield db_mock


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "medium",
        "status": "pending",
        "due_date": "2024-12-31T23:59:59Z"
    }


@pytest.fixture
def sample_task_response():
    """Sample task response data for testing."""
    return {
        "id": 1,
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "medium",
        "status": "pending",
        "due_date": "2024-12-31T23:59:59Z",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user_id": 1
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for testing."""
    return {"Authorization": "Bearer valid_token"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers for testing."""
    return {"Authorization": "Bearer invalid_token"}


class TestCreateTask:
    """Test cases for POST /tasks endpoint."""

    def test_create_task_success(self, client, mock_db, sample_task, sample_task_response, auth_headers):
        """Test successful task creation with valid data."""
        mock_db.execute.return_value.fetchone.return_value = sample_task_response
        
        response = client.post("/tasks", json=sample_task, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task["title"]
        assert data["description"] == sample_task["description"]
        assert data["priority"] == sample_task["priority"]
        assert data["status"] == sample_task["status"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_missing_title(self, client, auth_headers):
        """Test task creation fails with missing title."""
        task_data = {
            "description": "Task without title",
            "priority": "medium",
            "status": "pending"
        }
        
        response = client.post("/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data["detail"])

    def test_create_task_invalid_priority(self, client, auth_headers):
        """Test task creation fails with invalid priority."""
        task_data = {
            "title": "Test Task",
            "description": "Task with invalid priority",
            "priority": "invalid_priority",
            "status": "pending"
        }
        
        response = client.post("/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "priority" in str(data["detail"])

    def test_create_task_invalid_status(self, client, auth_headers):
        """Test task creation fails with invalid status."""
        task_data = {
            "title": "Test Task",
            "description": "Task with invalid status",
            "priority": "medium",
            "status": "invalid_status"
        }
        
        response = client.post("/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "status" in str(data["detail"])

    def test_create_task_title_too_long(self, client, auth_headers):
        """Test task creation fails with title exceeding maximum length."""
        task_data = {
            "title": "x" * 201,  # Exceeds 200 character limit
            "description": "Task with long title",
            "priority": "medium",
            "status": "pending"
        }
        
        response = client.post("/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "title" in str(data["detail"])

    def test_create_task_invalid_due_date_format(self, client, auth_headers):
        """Test task creation fails with invalid due date format."""
        task_data = {
            "title": "Test Task",
            "description": "Task with invalid due date",
            "priority": "medium",
            "status": "pending",
            "due_date": "invalid-date-format"
        }
        
        response = client.post("/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "due_date" in str(data["detail"])

    def test_create_task_unauthorized(self, client, sample_task):
        """Test task creation fails without authentication."""
        response = client.post("/tasks", json=sample_task)
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert "authentication required" in data["message"].lower()

    def test_create_task_invalid_token(self, client, sample_task, invalid_auth_headers):
        """Test task creation fails with invalid authentication token."""
        response = client.post("/tasks", json=sample_task, headers=invalid_auth_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_TOKEN"

    def test_create_task_database_error(self, client, mock_db, sample_task, auth_headers):
        """Test task creation handles database errors gracefully."""
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        response = client.post("/tasks", json=sample_task, headers=auth_headers)
        
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "INTERNAL_ERROR"


class TestGetTasks:
    """Test cases for GET /tasks endpoint."""

    def test_get_tasks_success(self, client, mock_db, auth_headers):
        """Test successful retrieval of tasks list."""
        mock_tasks = [
            {"id": 1, "title": "Task 1", "status": "pending", "priority": "high"},
            {"id": 2, "title": "Task 2", "status": "completed", "priority": "medium"}
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_tasks
        mock_db.execute.return_value.fetchone.return_value = {"total": 2}
        
        response = client.get("/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["tasks"]) == 2
        assert data["total"] == 2

    def test_