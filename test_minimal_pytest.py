"""Minimal pytest test to see if pytest itself works."""
import pytest

@pytest.mark.e2e
def test_minimal():
    """Simplest possible test."""
    print("\n✓ Test is running!")
    assert True
    print("✓ Test completed!")
