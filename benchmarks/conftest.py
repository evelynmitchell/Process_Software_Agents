"""Pytest configuration for benchmarks."""


def pytest_configure(config):
    """Configure pytest for benchmarking."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU (deselect with '-m \"not gpu\"')"
    )


def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Add custom information to benchmark JSON output."""
    import platform
    import sys

    output_json["python_version"] = sys.version
    output_json["python_implementation"] = platform.python_implementation()
    output_json["platform"] = platform.platform()
    output_json["processor"] = platform.processor()
