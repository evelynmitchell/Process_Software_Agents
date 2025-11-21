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
def mock_auth_user():
    """Mock authenticated user for testing."""
    return {
        "user_id": "user123",
        "username": "testuser",
        "email": "test@example.com"
    }


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
def sample_tasks_list():
    """Sample list of tasks for testing pagination and filtering."""
    return [
        {
            "id": "task1",
            "title": "High Priority Task",
            "description": "Urgent task",
            "priority": "high",
            "status": "pending",
            "due_date": "2024-01-15T10:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "user_id": "user123"
        },
        {
            "id": "task2",
            "title": "Medium Priority Task",
            "description": "Regular task",
            "priority": "medium",
            "status": "in_progress",
            "due_date": "2024-02-15T10:00:00Z",
            "created_at": "2024-01-02T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "user_id": "user123"
        },
        {
            "id": "task3",
            "title": "Low Priority Task",
            "description": "Optional task",
            "priority": "low",
            "status": "completed",
            "due_date": "2024-03-15T10:00:00Z",
            "created_at": "2024-01-03T00:00:00Z",
            "updated_at": "2024-01-03T00:00:00Z",
            "user_id": "user123"
        }
    ]


class TestCreateTask:
    """Test cases for POST /tasks endpoint."""

    @patch('src.api.tasks.get_current_user')
    @patch('src.api.tasks.create_task_service')
    def test_create_task_success(self, mock_create_service, mock_get_user, client, mock_auth_user, sample_task):
        """Test successful task creation with valid data."""
        mock_get_user.return_value = mock_auth_user
        created_task = {**sample_task, "id": "task123", "user_id": "user123", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"}
        mock_create_service.return_value = created_task

        response = client.post("/tasks", json=sample_task, headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "task123"
        assert data["title"] == sample_task["title"]
        assert data["description"] == sample_task["description"]
        assert data["priority"] == sample_task["priority"]
        assert data["status"] == sample_task["status"]
        assert data["user_id"] == "user123"
        mock_create_service.assert_called_once()

    @patch('src.api.tasks.get_current_user')
    def test_create_task_missing_title(self, mock_get_user, client, mock_auth_user):
        """Test task creation fails with missing title."""
        mock_get_user.return_value = mock_auth_user
        invalid_task = {
            "description": "Task without title",
            "priority": "medium",
            "status": "pending"
        }

        response = client.post("/tasks", json=invalid_task, headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("title" in str(error).lower() for error in data["detail"])

    @patch('src.api.tasks.get_current_user')
    def test_create_task_invalid_priority(self, mock_get_user, client, mock_auth_user):
        """Test task creation fails with invalid priority value."""
        mock_get_user.return_value = mock_auth_user
        invalid_task = {
            "title": "Test Task",
            "description": "Task with invalid priority",
            "priority": "invalid_priority",
            "status": "pending"
        }

        response = client.post("/tasks", json=invalid_task, headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch('src.api.tasks.get_current_user')
    def test_create_task_invalid_status(self, mock_get_user, client, mock_auth_user):
        """Test task creation fails with invalid status value."""
        mock_get_user.return_value = mock_auth_user
        invalid_task = {
            "title": "Test Task",
            "description": "Task with invalid status",
            "priority": "medium",
            "status": "invalid_status"
        }

        response = client.post("/tasks", json=invalid_task, headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch('src.api.tasks.get_current_user')
    def test_create_task_title_too_long(self, mock_get_user, client, mock_auth_user):
        """Test task creation fails with title exceeding maximum length."""
        mock_get_user.return_value = mock_auth_user
        invalid_task = {
            "title": "x" * 201,  # Assuming max length is 200
            "description": "Task with long title",
            "priority": "medium",
            "status": "pending"
        }

        response = client.post("/tasks", json=invalid_task, headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_task_unauthorized(self, client, sample_task):
        """Test task creation fails without authentication."""
        response = client.post("/tasks", json=sample_task)

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    @patch('src.api.tasks.get_current_user')
    def test_create_task_invalid_token(self, mock_get_user, client, sample_task):
        """Test task creation fails with invalid token."""
        mock_get_user.side_effect = Exception("Invalid token")

        response = client.post("/tasks", json=sample_task, headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401

    @patch('src.api.tasks.get_current_user')
    def test_create_task_empty_request_body(self, mock_get_