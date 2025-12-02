"""
Tests for the Web UI.
"""

from starlette.testclient import TestClient

from asp.web.main import app

client = TestClient(app)


def test_root_route():
    """Test that the root route returns 200 OK and contains persona links."""
    response = client.get("/")
    assert response.status_code == 200
    assert "ASP Platform" in response.text
    assert "Sarah" in response.text
    assert "Alex" in response.text
    assert "Jordan" in response.text


def test_developer_route():
    """Test that the developer route returns 200 OK and the Flow State Canvas."""
    response = client.get("/developer")
    assert response.status_code == 200
    assert "Flow State Canvas" in response.text
    assert "Active Tasks" in response.text
    assert "Recent Activity" in response.text
