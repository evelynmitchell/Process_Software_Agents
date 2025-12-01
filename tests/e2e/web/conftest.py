"""
Pytest fixtures for Web UI E2E tests with Playwright.

Provides server startup/shutdown and browser page fixtures.
"""

import socket
import threading
import time
from collections.abc import Generator

import pytest


def find_free_port() -> int:
    """Find a free port to run the test server on."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    """Wait for the server to be ready to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            time.sleep(0.2)
    return False


class ServerThread(threading.Thread):
    """Thread that runs the uvicorn server."""

    def __init__(self, port: int):
        super().__init__(daemon=True)
        self.port = port
        self.server = None

    def run(self):
        """Run the server in this thread."""
        import uvicorn

        from src.asp.web import app
        from src.asp.web.data import init_database, insert_demo_data

        # Initialize database with demo data
        init_database()
        insert_demo_data()

        # Create server config
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        """Signal the server to stop."""
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="session")
def server_port() -> int:
    """Get a free port for the test server."""
    return find_free_port()


@pytest.fixture(scope="session")
def web_server(server_port: int) -> Generator[str, None, None]:
    """
    Start the web server for testing.

    Yields the base URL of the running server.
    """
    # Start server in a background thread
    server_thread = ServerThread(server_port)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server(server_port, timeout=15.0):
        server_thread.stop()
        pytest.fail(f"Server failed to start on port {server_port} within timeout")

    base_url = f"http://127.0.0.1:{server_port}"
    yield base_url

    # Cleanup - signal server to stop
    server_thread.stop()
    server_thread.join(timeout=5)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }
