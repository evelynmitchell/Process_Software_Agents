"""
Integration tests for task management endpoints

Tests authentication, authorization, and CRUD operations for task management API.
Covers all endpoints with various scenarios including edge cases and error conditions.

Component ID: COMP-003
Semantic Unit: SU-003

Author: ASP Code Agent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.api.tasks import app
from tests.conftest import (
    create_test_user,
    create_test_task,
    get_auth_headers,
    cleanup_test_data
)


class TestTasksAPI:
    """Integration tests for task management API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self.client = TestClient(app)
        self.test_user_id = None
        self.test_task_ids = []
        yield
        # Cleanup after each test
        cleanup_test_data(self.test_user_id, self.test_task_ids)

    def _create_authenticated_user(self) -> Dict[str, Any]:
        """Create a test user and return user data with auth headers."""
        user_data = create_test_user()
        self.test_user_id = user_data["id"]
        return user_data

    def _create_test_task(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Create a test task and track for cleanup."""
        task_data = create_test_task(user_id, **kwargs)
        self.test_task_ids.append(task_data["id"])
        return task_data


class TestCreateTask(TestTasksAPI):
    """Tests for POST /tasks endpoint."""

    def test_create_task_success(self):
        """Test successful task creation with valid data."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": "Test Task",
            "description": "Test task description",
            "priority": "medium",
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["due_date"] == task_data["due_date"]
        assert data["status"] == "pending"
        assert data["user_id"] == user["id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        self.test_task_ids.append(data["id"])

    def test_create_task_minimal_data(self):
        """Test task creation with only required fields."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": "Minimal Task"
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] is None
        assert data["priority"] == "medium"  # default value
        assert data["due_date"] is None
        assert data["status"] == "pending"
        
        self.test_task_ids.append(data["id"])

    def test_create_task_invalid_title_empty(self):
        """Test task creation fails with empty title."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": ""
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "title" in data["message"].lower()

    def test_create_task_invalid_title_too_long(self):
        """Test task creation fails with title exceeding 200 characters."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": "x" * 201
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "title" in data["message"].lower()

    def test_create_task_invalid_priority(self):
        """Test task creation fails with invalid priority value."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": "Test Task",
            "priority": "invalid"
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "priority" in data["message"].lower()

    def test_create_task_invalid_due_date_format(self):
        """Test task creation fails with invalid due date format."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        task_data = {
            "title": "Test Task",
            "due_date": "invalid-date"
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "due_date" in data["message"].lower()

    def test_create_task_due_date_in_past(self):
        """Test task creation fails with due date in the past."""
        user = self._create_authenticated_user()
        headers = get_auth_headers(user["token"])
        
        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        task_data = {
            "title": "Test Task",
            "due_date": past_date
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "INVALID_DUE_DATE"
        assert "past" in data["message"].lower()

    def test_create_task_no_authentication(self):
        """Test task creation fails without authentication."""
        task_data = {
            "title": "Test Task"
        }
        
        response = self.client.post("/tasks", json=task_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "AUTHENTICATION_REQUIRED"

    def test_create_task_invalid_token(self):
        """Test task creation fails with invalid authentication token."""
        headers = {"Authorization": "Bearer invalid-token"}
        task_data = {
            "title": "Test Task"
        }
        
        response = self.client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "INVALID_TOKEN"


class TestGetTasks(TestTasksAPI):
    """Tests for GET /tasks endpoint."""

    def test_get_tasks_empty_