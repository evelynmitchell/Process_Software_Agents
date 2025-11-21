"""
Integration tests for task management endpoints

Tests authentication, authorization, and CRUD operations for task management API.
Covers all endpoints with various scenarios including edge cases and error conditions.

Component ID: COMP-003
Semantic Unit: SU-003

Author: ASP Code Generator
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

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
        self.test_users = []
        self.test_tasks = []
        yield
        # Cleanup after each test
        cleanup_test_data(self.test_users, self.test_tasks)

    def test_create_task_success(self):
        """Test successful task creation with valid data."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "medium",
            "due_date": "2024-12-31T23:59:59Z"
        }
        
        response = self.client.post("/api/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["status"] == "pending"
        assert data["user_id"] == user["id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        self.test_tasks.append(data)

    def test_create_task_missing_title(self):
        """Test task creation fails with missing title."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        task_data = {
            "description": "This is a test task",
            "priority": "medium"
        }
        
        response = self.client.post("/api/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "title" in data["message"].lower()

    def test_create_task_invalid_priority(self):
        """Test task creation fails with invalid priority."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "invalid_priority"
        }
        
        response = self.client.post("/api/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "priority" in data["message"].lower()

    def test_create_task_invalid_due_date(self):
        """Test task creation fails with invalid due date format."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "medium",
            "due_date": "invalid-date"
        }
        
        response = self.client.post("/api/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "due_date" in data["message"].lower()

    def test_create_task_unauthorized(self):
        """Test task creation fails without authentication."""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "medium"
        }
        
        response = self.client.post("/api/tasks", json=task_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    def test_create_task_invalid_token(self):
        """Test task creation fails with invalid authentication token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "medium"
        }
        
        response = self.client.post("/api/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_TOKEN"

    def test_get_tasks_success(self):
        """Test successful retrieval of user's tasks."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        # Create test tasks
        task1 = create_test_task(user["id"], "Task 1", "high")
        task2 = create_test_task(user["id"], "Task 2", "low")
        self.test_tasks.extend([task1, task2])
        
        response = self.client.get("/api/tasks", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["tasks"]) == 2
        assert data["total"] == 2

    def test_get_tasks_with_pagination(self):
        """Test task retrieval with pagination parameters."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        # Create multiple test tasks
        tasks = []
        for i in range(5):
            task = create_test_task(user["id"], f"Task {i+1}", "medium")
            tasks.append(task)
        self.test_tasks.extend(tasks)
        
        response = self.client.get("/api/tasks?page=1&per_page=2", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_get_tasks_with_status_filter(self):
        """Test task retrieval with status filter."""
        user = create_test_user("testuser", "test@example.com")
        self.test_users.append(user)
        headers = get_auth_headers(user["id"])
        
        # Create tasks with different statuses
        task1 = create_test_task(user["id"], "Pending Task", "medium", status="pending")
        task2 = create_test_task(user["id"], "Completed Task", "medium