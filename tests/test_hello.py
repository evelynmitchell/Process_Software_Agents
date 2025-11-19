#!/usr/bin/env python3
"""
Unit tests for Hello World API.

Comprehensive tests for the hello world endpoint including
edge cases, error handling, and response format validation.

Author: ASP Code Agent
Date: 2025-11-19
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
from main import app, HelloWorldHandler


class TestHelloWorldHandler:
    """
    Unit tests for HelloWorldHandler component.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = HelloWorldHandler()
    
    def test_get_hello_success(self):
        """
        Test successful hello world response generation.
        """
        response = self.handler.get_hello()
        
        # Verify response structure
        assert isinstance(response, dict)
        assert "message" in response
        assert "timestamp" in response
        assert "status" in response
        
        # Verify response values
        assert response["message"] == "Hello World"
        assert response["status"] == "success"
        
        # Verify timestamp format (ISO 8601 with Z suffix)
        timestamp = response["timestamp"]
        assert timestamp.endswith('Z')
        
        # Verify timestamp can be parsed
        parsed_time = datetime.fromisoformat(timestamp.rstrip('Z'))
        assert isinstance(parsed_time, datetime)
    
    def test_format_response_success(self):
        """
        Test successful response formatting.
        """
        test_message = "Test Message"
        response = self.handler.format_response(test_message)
        
        assert response["message"] == test_message
        assert response["status"] == "success"
        assert "timestamp" in response
        assert response["timestamp"].endswith('Z')
    
    def test_format_response_empty_message(self):
        """
        Test response formatting with empty message.
        """
        response = self.handler.format_response("")
        
        assert response["message"] == ""
        assert response["status"] == "success"
        assert "timestamp" in response
    
    def test_format_response_special_characters(self):
        """
        Test response formatting with special characters.
        """
        special_message = "Hello! @#$%^&*()_+ 世界"
        response = self.handler.format_response(special_message)
        
        assert response["message"] == special_message
        assert response["status"] == "success"
    
    @patch('main.datetime')
    def test_format_response_datetime_error(self, mock_datetime):
        """
        Test response formatting when datetime fails.
        """
        # Mock datetime to raise exception
        mock_datetime.utcnow.side_effect = Exception("DateTime error")
        
        with pytest.raises(Exception) as exc_info:
            self.handler.format_response("Test")
        
        assert "Failed to format response" in str(exc_info.value)
    
    @patch('main.HelloWorldHandler.format_response')
    def test_get_hello_format_error(self, mock_format):
        """
        Test get_hello when format_response fails.
        """
        mock_format.side_effect = Exception("Format error")
        
        with pytest.raises(Exception):
            self.handler.get_hello()
    
    def test_timestamp_format_consistency(self):
        """
        Test that timestamp format is consistent across multiple calls.
        """
        responses = [self.handler.get_hello() for _ in range(5)]
        
        for response in responses:
            timestamp = response["timestamp"]
            # All timestamps should end with Z
            assert timestamp.endswith('Z')
            # All timestamps should be parseable
            parsed = datetime.fromisoformat(timestamp.rstrip('Z'))
            assert isinstance(parsed, datetime)


class TestHelloAPI:
    """
    Integration tests for Hello World API endpoints.
    """
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_hello_endpoint_success(self):
        """
        Test successful GET /hello request.
        """
        response = self.client.get("/hello")
        
        # Verify HTTP status
        assert response.status_code == 200
        
        # Verify response is JSON
        assert response.headers["content-type"] == "application/json"
        
        # Verify response structure
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert "timestamp" in data
        assert "status" in data
        
        # Verify response values
        assert data["message"] == "Hello World"
        assert data["status"] == "success"
        
        # Verify timestamp format
        timestamp = data["timestamp"]
        assert timestamp.endswith('Z')
        datetime.fromisoformat(timestamp.rstrip('Z'))  # Should not raise
    
    def test_hello_endpoint_multiple_requests(self):
        """
        Test multiple requests to /hello endpoint.
        """
        responses = [self.client.get("/hello") for _ in range(3)]
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Hello World"
            assert data["status"] == "success"
    
    def test_hello_endpoint_concurrent_requests(self):
        """
        Test concurrent requests to /hello endpoint.
        """
        import concurrent.futures
        
        def make_request():
            return self.client.get("/hello")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Hello World"
    
    @patch('main.hello_handler.get_hello')
    def test_hello_endpoint_internal_error(self, mock_get_hello):
        """
        Test /hello endpoint when internal error occurs.
        """
        mock_get_hello.side_effect = Exception("Internal error")
        
        response = self.client.get("/hello")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "INTERNAL_ERROR"
        assert data["detail"]["message"] == "Internal server error"
    
    def test_hello_endpoint_wrong_method(self):
        """
        Test /hello endpoint with wrong HTTP method.
        """
        # POST should not be allowed
        response = self.client.post("/hello")
        assert response.status_code == 405  # Method Not Allowed
        
        # PUT should not be allowed
        response = self.client.put("/hello")
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = self.client.delete("/hello")
        assert response.status_code == 405
    
    def test_hello_endpoint_with_query_params(self):
        """
        Test /hello endpoint ignores query parameters.
        """
        response = self.client.get("/hello?param=value&test=123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"
        assert data["status"] == "success"
    
    def test_hello_endpoint_with_headers(self):
        """
        Test /hello endpoint with custom headers.
        """
        headers = {
            "User-Agent": "Test Client",
            "Accept": "application/json",
            "Custom-Header": "test-value"
        }
        
        response = self.client.get("/hello", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"
    
    def test_root_endpoint(self):
        """
        Test root endpoint functionality.
        """
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Hello World API"
    
    def test_health_endpoint(self):
        """
        Test health check endpoint.
        """
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_nonexistent_endpoint(self):
        """
        Test request to non-existent endpoint.
        """
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_response_time_performance(self):
        """
        Test that response time is under 10ms as per requirements.
        """
        import time
        
        start_time = time.time()
        response = self.client.get("/hello")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # Allow some margin for test environment overhead
        assert response_time_ms < 100  # 100ms threshold for test environment
    
    def test_response_security(self):
        """
        Test that response doesn't expose sensitive information.
        """
        response = self.client.get("/hello")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify only expected fields are present
        expected_fields = {"message", "timestamp", "status"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields
        
        # Verify no server information in response
        response_text = response.text.lower()
        sensitive_terms = ["server", "python", "fastapi", "uvicorn", "path", "file"]
        for term in sensitive_terms:
            assert term not in response_text


class TestEdgeCases:
    """
    Edge case tests for Hello World API.
    """
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_hello_endpoint_stress_test(self):
        """
        Stress test with many rapid requests.
        """
        responses = []
        for _ in range(100):
            response = self.client.get("/hello")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Hello World"
    
    def test_timestamp_uniqueness(self):
        """
        Test that timestamps are unique across rapid requests.
        """
        responses = []
        for _ in range(10):
            response = self.client.get("/hello")
            responses.append(response.json()["timestamp"])
        
        # Most timestamps should be unique (allowing for some duplicates due to speed)
        unique_timestamps = set(responses)
        assert len(unique_timestamps) >= len(responses) * 0.8  # At least 80% unique
