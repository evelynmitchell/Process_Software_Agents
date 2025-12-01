#!/usr/bin/env python3
"""
Test Execution Script for All 21 Agents
Based on Comprehensive Agent Test Plan v1.0.0

Usage:
    python scripts/run_agent_tests.py [command]

Commands:
    all                 Run all tests (default)
    core                Run core agent tests (7 agents)
    orchestrators       Run orchestrator tests (2 agents)
    design-specialists  Run design review specialist tests (6 agents)
    code-specialists    Run code review specialist tests (6 agents)
    integration         Run integration/E2E tests
    performance         Run performance tests
    unit                Run all unit tests
    e2e                 Run all E2E tests
    coverage            Run all tests with coverage report
    incremental         Run all tests incrementally (recommended)
"""

import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


class TestRunner:
    """Test runner for ASP Platform agents"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"

    def print_header(self, text: str) -> None:
        """Print section header"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}{text}{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

    def print_success(self, text: str) -> None:
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

    def print_error(self, text: str) -> None:
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.NC}")

    def print_info(self, text: str) -> None:
        """Print info message"""
        print(f"{Colors.YELLOW}➜ {text}{Colors.NC}")

    def check_env_vars(self) -> bool:
        """Check required environment variables"""
        self.print_header("Checking Environment Variables")

        required_vars = [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            self.print_error(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )
            self.print_info("Please set the following variables:")
            for var in missing_vars:
                print(f'  export {var}="your_key_here"')
            return False

        self.print_success("All environment variables set")
        return True

    def run_pytest(
        self,
        test_path: str,
        description: str | None = None,
        extra_args: list[str] | None = None,
    ) -> bool:
        """Run pytest with specified path and arguments"""
        if description:
            self.print_info(description)

        cmd = ["pytest", test_path, "-v", "--tb=short"]
        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.print_error(f"Tests failed with exit code {e.returncode}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests"""
        self.print_header("Running ALL Tests (21 Agents)")
        return self.run_pytest("tests/")

    def run_core_agents(self) -> bool:
        """Run core agent tests (7 agents)"""
        self.print_header("Phase 1: Core Agents (7 Agents)")

        tests = [
            (
                "tests/unit/test_agents/test_planning_agent.py",
                "Testing Planning Agent (FR-1)...",
            ),
            ("tests/e2e/test_planning_agent_e2e.py", "Testing Planning Agent E2E..."),
            (
                "tests/unit/test_agents/test_design_agent.py",
                "Testing Design Agent (FR-2)...",
            ),
            ("tests/e2e/test_design_agent_e2e.py", "Testing Design Agent E2E..."),
            (
                "tests/unit/test_agents/test_design_review_agent.py",
                "Testing Design Review Agent (FR-3)...",
            ),
            (
                "tests/e2e/test_design_review_agent_e2e.py",
                "Testing Design Review Agent E2E...",
            ),
            (
                "tests/unit/test_agents/test_code_agent.py",
                "Testing Code Agent (FR-4)...",
            ),
            ("tests/e2e/test_code_agent_e2e.py", "Testing Code Agent E2E..."),
            (
                "tests/unit/test_agents/test_code_review_orchestrator.py",
                "Testing Code Review Agent (FR-5)...",
            ),
            (
                "tests/unit/test_agents/test_test_agent.py",
                "Testing Test Agent (FR-6)...",
            ),
            (
                "tests/unit/test_agents/test_postmortem_agent.py",
                "Testing Postmortem Agent (FR-7)...",
            ),
        ]

        for test_path, description in tests:
            full_path = self.project_root / test_path
            if not full_path.exists():
                self.print_info(f"Skipping {test_path} (not found)")
                continue

            if not self.run_pytest(test_path, description):
                return False

        self.print_success("All Core Agents tested successfully!")
        return True

    def run_orchestrators(self) -> bool:
        """Run orchestrator tests (2 agents)"""
        self.print_header("Phase 2: Orchestrator Agents (2 Agents)")

        tests = [
            (
                "tests/unit/test_agents/test_design_review_orchestrator.py",
                "Testing Design Review Orchestrator...",
            ),
            (
                "tests/unit/test_agents/test_code_review_orchestrator.py",
                "Testing Code Review Orchestrator...",
            ),
        ]

        for test_path, description in tests:
            full_path = self.project_root / test_path
            if not full_path.exists():
                self.print_info(f"Skipping {test_path} (not found)")
                continue

            if not self.run_pytest(test_path, description):
                return False

        self.print_success("All Orchestrator Agents tested successfully!")
        return True

    def run_design_specialists(self) -> bool:
        """Run design review specialist tests (6 agents)"""
        self.print_header("Phase 3: Design Review Specialists (6 Agents)")

        test_path = "tests/unit/test_agents/reviews/"
        full_path = self.project_root / test_path

        if not full_path.exists():
            self.print_info(f"Skipping {test_path} (not found)")
            return True

        if not self.run_pytest(test_path, "Testing all design review specialists..."):
            return False

        self.print_success("All Design Review Specialists tested successfully!")
        return True

    def run_code_specialists(self) -> bool:
        """Run code review specialist tests (6 agents)"""
        self.print_header("Phase 4: Code Review Specialists (6 Agents)")

        test_path = "tests/unit/test_agents/code_reviews/"
        full_path = self.project_root / test_path

        if not full_path.exists():
            self.print_info(f"Skipping {test_path} (not found)")
            return True

        if not self.run_pytest(test_path, "Testing all code review specialists..."):
            return False

        self.print_success("All Code Review Specialists tested successfully!")
        return True

    def run_integration_tests(self) -> bool:
        """Run integration/E2E tests"""
        self.print_header("Phase 5: Integration & E2E Tests")

        test_path = "tests/e2e/"
        full_path = self.project_root / test_path

        if not full_path.exists():
            self.print_info(f"Skipping {test_path} (not found)")
            return True

        if not self.run_pytest(test_path, "Testing end-to-end workflows..."):
            return False

        self.print_success("All integration tests passed successfully!")
        return True

    def run_performance_tests(self) -> bool:
        """Run performance tests"""
        self.print_header("Phase 6: Performance Tests")

        test_path = "tests/performance/"
        full_path = self.project_root / test_path

        if not full_path.exists():
            self.print_info(f"No performance tests found ({test_path} doesn't exist)")
            return True

        if not self.run_pytest(test_path, "Testing agent performance..."):
            return False

        self.print_success("Performance tests passed successfully!")
        return True

    def run_unit_tests(self) -> bool:
        """Run unit tests only"""
        self.print_header("Running Unit Tests Only")
        return self.run_pytest("tests/unit/")

    def run_e2e_tests(self) -> bool:
        """Run E2E tests only"""
        self.print_header("Running E2E Tests Only")
        return self.run_pytest("tests/e2e/")

    def run_with_coverage(self) -> bool:
        """Run all tests with coverage report"""
        self.print_header("Running All Tests with Coverage Report")
        extra_args = ["--cov=src/asp", "--cov-report=html", "--cov-report=term"]
        success = self.run_pytest("tests/", extra_args=extra_args)

        if success:
            self.print_success("Coverage report generated in htmlcov/index.html")

        return success

    def run_incremental(self) -> bool:
        """Run all tests incrementally (phase by phase)"""
        self.print_header("Running Incremental Test Suite (All 21 Agents)")

        phases = [
            ("Core Agents", self.run_core_agents),
            ("Orchestrators", self.run_orchestrators),
            ("Design Specialists", self.run_design_specialists),
            ("Code Specialists", self.run_code_specialists),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
        ]

        for phase_name, phase_func in phases:
            if not phase_func():
                self.print_error(f"{phase_name} phase failed")
                return False

        self.print_success("All 21 agents tested successfully!")
        return True

    def print_usage(self) -> None:
        """Print usage information"""
        print(__doc__)

    def run(self, command: str) -> int:
        """Run the specified test command"""
        # Check environment variables first
        if not self.check_env_vars():
            return 1

        # Execute command
        commands = {
            "all": self.run_all_tests,
            "core": self.run_core_agents,
            "orchestrators": self.run_orchestrators,
            "design-specialists": self.run_design_specialists,
            "code-specialists": self.run_code_specialists,
            "integration": self.run_integration_tests,
            "performance": self.run_performance_tests,
            "unit": self.run_unit_tests,
            "e2e": self.run_e2e_tests,
            "coverage": self.run_with_coverage,
            "incremental": self.run_incremental,
            "help": lambda: (self.print_usage(), True)[1],
        }

        if command not in commands:
            self.print_error(f"Unknown command: {command}")
            self.print_usage()
            return 1

        success = commands[command]()

        if success:
            self.print_header("Test Execution Complete")
            self.print_success("All requested tests completed successfully!")
            return 0
        else:
            self.print_header("Test Execution Failed")
            self.print_error("Some tests failed. Please check the output above.")
            return 1


def main():
    """Main entry point"""
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    runner = TestRunner()
    exit_code = runner.run(command)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
