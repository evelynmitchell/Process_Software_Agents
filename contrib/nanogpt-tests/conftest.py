"""Pytest configuration and fixtures for nanoGPT tests."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def small_config():
    """Provide small GPTConfig for fast testing.

    This config creates a tiny model (~50K params) that runs quickly on CPU.
    """
    from model import GPTConfig
    return GPTConfig(
        block_size=32,
        vocab_size=100,
        n_layer=2,
        n_head=4,
        n_embd=64,
        dropout=0.0,
        bias=True
    )


@pytest.fixture
def tiny_config():
    """Provide tiny GPTConfig for integration tests.

    Even smaller than small_config for tests that need to train.
    """
    from model import GPTConfig
    return GPTConfig(
        block_size=16,
        vocab_size=50,
        n_layer=1,
        n_head=2,
        n_embd=32,
        dropout=0.0,
        bias=True
    )
