"""hellogit demonstration: End-to-end test of workspace isolation workflow.

This test demonstrates the complete workspace isolation architecture from ADR 001:
1. Create isolated workspace
2. Initialize simple git repo (hellogit)
3. Make changes via ASP workflow
4. Verify workspace isolation
5. Cleanup

This proves that ASP can work on ANY repository without cluttering Process_Software_Agents.

See: design/ADR_001_workspace_isolation_and_execution_tracking.md
"""

import pytest
from pathlib import Path

from src.services.workspace_manager import WorkspaceManager


class TestHelloGitWorkflow:
    """Demonstration of working on a simple project in isolated workspace."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Provide WorkspaceManager with temporary base."""
        return WorkspaceManager(base_path=tmp_path / "hellogit-workspaces")

    def test_hellogit_complete_workflow(self, manager):
        """Complete workflow: create hello git project, modify it, cleanup.

        This demonstrates:
        - Workspace isolation (not in Process_Software_Agents)
        - Git repository initialization
        - Making changes and commits
        - Clean cleanup

        This is the foundation for working on external repos.
        """
        # Step 1: Create workspace
        workspace = manager.create_workspace("hellogit-demo-001")
        assert workspace.path.exists()
        assert not (Path.cwd() / "hellogit").exists()  # Not in current dir!

        # Step 2: Initialize a simple "hello git" project
        initial_files = {
            "README.md": "# Hello Git\n\nA simple demo project.\n",
            "hello.py": "def hello():\n    print('Hello, Git!')\n",
            ".gitignore": "*.pyc\n__pycache__/\n",
        }

        repo_path = manager.initialize_git_repo(workspace, initial_files=initial_files)

        # Verify files created
        assert (repo_path / "README.md").exists()
        assert (repo_path / "hello.py").exists()
        assert (repo_path / ".gitignore").exists()

        # Step 3: "ASP Agent" makes a change (simulated)
        # In real workflow, Planning/Design/Code agents would do this
        new_feature_code = '''def hello():
    """Say hello to the world."""
    print('Hello, Git!')

def goodbye():
    """Say goodbye."""
    print('Goodbye, Git!')
'''
        (repo_path / "hello.py").write_text(new_feature_code)

        # Add tests
        test_code = '''import hello

def test_hello():
    """Test hello function."""
    hello.hello()  # Should not raise

def test_goodbye():
    """Test goodbye function."""
    hello.goodbye()  # Should not raise
'''
        (repo_path / "test_hello.py").write_text(test_code)

        # Step 4: Commit changes (simulated agent commit)
        import subprocess

        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add goodbye function and tests"],
            cwd=str(repo_path),
            check=True,
        )

        # Step 5: Verify isolation - workspace is NOT in Process_Software_Agents
        process_software_agents_path = Path.cwd()
        assert not str(workspace.path).startswith(str(process_software_agents_path))
        assert str(workspace.path).startswith("/tmp") or str(workspace.path).startswith(
            str(Path.home())
        )

        # Step 6: Verify git history
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Initial commit" in result.stdout
        assert "Add goodbye function" in result.stdout

        # Step 7: Cleanup (workspace disappears completely)
        manager.cleanup_workspace(workspace)
        assert not workspace.path.exists()
        assert not repo_path.exists()

    def test_hellogit_multiple_workspaces_isolated(self, manager):
        """Test that multiple workspaces don't interfere with each other."""
        # Create two separate projects
        ws1 = manager.create_workspace("project-a")
        ws2 = manager.create_workspace("project-b")

        # Initialize different projects
        manager.initialize_git_repo(ws1, initial_files={"README.md": "# Project A\n"})
        manager.initialize_git_repo(ws2, initial_files={"README.md": "# Project B\n"})

        # Verify isolation
        assert (ws1.target_repo_path / "README.md").read_text() == "# Project A\n"
        assert (ws2.target_repo_path / "README.md").read_text() == "# Project B\n"

        # Cleanup both
        manager.cleanup_workspace(ws1)
        manager.cleanup_workspace(ws2)

    def test_hellogit_simulates_external_repo_workflow(self, manager):
        """Simulate the workflow for working on an external repository.

        This is what happens when ASP works on a real external repo:
        1. Clone repo (or initialize for this test)
        2. Create feature branch
        3. Make changes
        4. Commit
        5. (In real workflow: create PR in external repo)
        6. Cleanup workspace
        """
        import subprocess

        # Step 1: Create workspace (in real workflow, this is automatic)
        workspace = manager.create_workspace("external-repo-simulation")

        # Step 2: "Clone" repository (using init for this test)
        repo_path = manager.initialize_git_repo(
            workspace,
            initial_files={
                "README.md": "# External Project\n",
                "src/app.py": "# Main application\n",
            },
        )

        # Step 3: Create feature branch
        subprocess.run(
            ["git", "checkout", "-b", "feature/add-logging"],
            cwd=str(repo_path),
            check=True,
        )

        # Step 4: "ASP Agent" makes changes
        (repo_path / "src/logger.py").write_text(
            "import logging\n\nlogger = logging.getLogger(__name__)\n"
        )

        # Update app.py
        app_code = """# Main application
import logger

logger.logger.info("Application started")
"""
        (repo_path / "src/app.py").write_text(app_code)

        # Step 5: Commit changes
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add logging infrastructure"],
            cwd=str(repo_path),
            check=True,
        )

        # Step 6: Verify we're on feature branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "feature/add-logging"

        # Step 7: (In real workflow: create PR here)
        # pr_url = create_pr("org/external-repo", "feature/add-logging")

        # Step 8: Cleanup workspace
        manager.cleanup_workspace(workspace)
        assert not workspace.path.exists()


class TestHelloGitWithWorkDirectory:
    """Tests demonstrating the .asp/ working directory for artifacts."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Provide WorkspaceManager with temporary base."""
        return WorkspaceManager(base_path=tmp_path / "hellogit-workspaces")

    def test_asp_working_directory_for_artifacts(self, manager):
        """Demonstrate using .asp/ directory for execution artifacts.

        In real workflow:
        - Planning agent outputs go in .asp/planning.json
        - Design agent outputs go in .asp/design.json
        - Code review results go in .asp/code_review.json
        - These are ephemeral, not committed to target repo
        """
        workspace = manager.create_workspace("artifacts-demo")
        manager.initialize_git_repo(workspace, initial_files={"README.md": "# Demo\n"})

        # Simulate agent artifacts
        (workspace.asp_path / "planning.json").write_text('{"task": "add feature"}')
        (workspace.asp_path / "design.json").write_text('{"components": []}')
        (workspace.asp_path / "code_review.json").write_text('{"issues": []}')

        # Verify artifacts exist
        assert (workspace.asp_path / "planning.json").exists()
        assert (workspace.asp_path / "design.json").exists()
        assert (workspace.asp_path / "code_review.json").exists()

        # Verify artifacts are NOT in git repo
        repo_files = list(workspace.target_repo_path.rglob("*.json"))
        assert len(repo_files) == 0  # No JSON files in repo

        # Cleanup removes everything (repo + artifacts)
        manager.cleanup_workspace(workspace)
        assert not workspace.path.exists()
