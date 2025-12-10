#!/bin/bash
# Test Execution Script for All 21 Agents
# Based on Comprehensive Agent Test Plan v1.0.0
#
# Context-efficient backpressure pattern:
# - Default: Show summary only, full output on failure
# - VERBOSE=1: Show all output
# Reference: https://www.hlyr.dev/blog/context-efficient-backpressure

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERBOSE="${VERBOSE:-0}"
LOG_DIR="${LOG_DIR:-/tmp/agent_test_logs}"
mkdir -p "$LOG_DIR"

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info message
print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

# Use uv run python -m pytest for consistent environment
# This ensures pytest runs in the uv-managed venv, not system pytest
PYTEST_CMD="uv run python -m pytest"

# Context-efficient test runner
# Captures full output, shows summary on success, full log on failure
run_pytest() {
    local test_path="$1"
    local test_name="$2"
    local log_file="$LOG_DIR/${test_name//\//_}.log"

    if [ "$VERBOSE" = "1" ]; then
        # Verbose mode: stream everything
        $PYTEST_CMD "$test_path" -v --tb=short
    else
        # Quiet mode: capture output, show summary
        print_info "Running $test_name..."

        local exit_code=0
        if $PYTEST_CMD "$test_path" -v --tb=short > "$log_file" 2>&1; then
            # Success: show brief summary
            local passed=$(grep -oP '\d+(?= passed)' "$log_file" | tail -1 || echo "?")
            local duration=$(grep -oP '\d+\.\d+(?=s)' "$log_file" | tail -1 || echo "?")
            print_success "$test_name: ${passed} passed (${duration}s)"
        else
            exit_code=$?
            # Failure: show the relevant output
            print_error "$test_name FAILED"
            echo ""
            echo -e "${RED}═══ Test Output ═══${NC}"
            # Show failures and errors, skip the verbose pass lines
            grep -E "FAILED|ERROR|AssertionError|^E |short test summary|=== FAILURES ===" "$log_file" | head -50 || true
            echo ""
            echo -e "${RED}═══ Full log: $log_file ═══${NC}"
            return $exit_code
        fi
    fi
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv not found. Please install uv first."
    exit 1
fi

# Check environment variables
check_env_vars() {
    print_header "Checking Environment Variables"

    missing_required=()
    missing_optional=()

    # Required
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        missing_required+=("ANTHROPIC_API_KEY")
    fi

    # Optional (warn but don't fail)
    if [ -z "$LANGFUSE_PUBLIC_KEY" ]; then
        missing_optional+=("LANGFUSE_PUBLIC_KEY")
    fi

    if [ -z "$LANGFUSE_SECRET_KEY" ]; then
        missing_optional+=("LANGFUSE_SECRET_KEY")
    fi

    if [ ${#missing_required[@]} -gt 0 ]; then
        print_error "Missing required environment variables: ${missing_required[*]}"
        print_info "Please set the following variables:"
        for var in "${missing_required[@]}"; do
            echo "  export $var=\"your_key_here\""
        done
        exit 1
    fi

    if [ ${#missing_optional[@]} -gt 0 ]; then
        print_info "Optional variables not set: ${missing_optional[*]}"
        print_info "Some features (telemetry) may not work"
    fi

    print_success "Required environment variables set"
}

# Test suite functions
run_all_tests() {
    print_header "Running ALL Tests (21 Agents)"
    run_pytest "tests/" "all_tests"
}

run_core_agents() {
    print_header "Phase 1: Core Agents (7 Agents)"

    run_pytest "tests/unit/test_agents/test_planning_agent.py" "planning_agent_unit"
    run_pytest "tests/e2e/test_planning_agent_e2e.py" "planning_agent_e2e"

    run_pytest "tests/unit/test_agents/test_design_agent.py" "design_agent_unit"
    run_pytest "tests/e2e/test_design_agent_e2e.py" "design_agent_e2e"

    run_pytest "tests/unit/test_agents/test_design_review_agent.py" "design_review_agent_unit"
    run_pytest "tests/e2e/test_design_review_agent_e2e.py" "design_review_agent_e2e"

    run_pytest "tests/unit/test_agents/test_code_agent.py" "code_agent_unit"
    run_pytest "tests/e2e/test_code_agent_e2e.py" "code_agent_e2e"

    run_pytest "tests/unit/test_agents/test_code_review_orchestrator.py" "code_review_orchestrator"

    run_pytest "tests/unit/test_agents/test_test_agent.py" "test_agent"

    run_pytest "tests/unit/test_agents/test_postmortem_agent.py" "postmortem_agent"

    print_success "All Core Agents tested successfully!"
}

run_orchestrators() {
    print_header "Phase 2: Orchestrator Agents (2 Agents)"

    run_pytest "tests/unit/test_agents/test_design_review_orchestrator.py" "design_review_orchestrator"
    run_pytest "tests/unit/test_agents/test_code_review_orchestrator.py" "code_review_orchestrator"

    print_success "All Orchestrator Agents tested successfully!"
}

run_design_specialists() {
    print_header "Phase 3: Design Review Specialists (6 Agents)"

    run_pytest "tests/unit/test_agents/reviews/" "design_review_specialists"

    print_success "All Design Review Specialists tested successfully!"
}

run_code_specialists() {
    print_header "Phase 4: Code Review Specialists (6 Agents)"

    run_pytest "tests/unit/test_agents/code_reviews/" "code_review_specialists"

    print_success "All Code Review Specialists tested successfully!"
}

run_integration_tests() {
    print_header "Phase 5: Integration & E2E Tests"

    run_pytest "tests/e2e/" "e2e_integration"

    print_success "All integration tests passed successfully!"
}

run_performance_tests() {
    print_header "Phase 6: Performance Tests"

    if [ -d "tests/performance" ]; then
        run_pytest "tests/performance/" "performance"
        print_success "Performance tests passed successfully!"
    else
        print_info "No performance tests found (tests/performance/ doesn't exist)"
    fi
}

run_unit_tests() {
    print_header "Running Unit Tests Only"
    run_pytest "tests/unit/" "unit_tests"
}

run_e2e_tests() {
    print_header "Running E2E Tests Only"
    run_pytest "tests/e2e/" "e2e_tests"
}

run_with_coverage() {
    print_header "Running All Tests with Coverage Report"
    local log_file="$LOG_DIR/coverage.log"

    if [ "$VERBOSE" = "1" ]; then
        $PYTEST_CMD tests/ -v --cov=src/asp --cov-report=html --cov-report=term --tb=short
    else
        print_info "Running tests with coverage..."
        if $PYTEST_CMD tests/ -v --cov=src/asp --cov-report=html --cov-report=term --tb=short > "$log_file" 2>&1; then
            # Extract coverage summary
            local coverage=$(grep -oP 'TOTAL\s+\d+\s+\d+\s+\K\d+%' "$log_file" || echo "?")
            local passed=$(grep -oP '\d+(?= passed)' "$log_file" | tail -1 || echo "?")
            print_success "Coverage: $coverage, Tests: $passed passed"
            print_info "Full report: htmlcov/index.html"
        else
            print_error "Tests failed"
            echo ""
            grep -E "FAILED|ERROR|coverage" "$log_file" | head -30 || true
            echo ""
            echo -e "${RED}═══ Full log: $log_file ═══${NC}"
            return 1
        fi
    fi
}

run_incremental() {
    print_header "Running Incremental Test Suite (All 21 Agents)"
    run_core_agents
    run_orchestrators
    run_design_specialists
    run_code_specialists
    run_integration_tests
    run_performance_tests
    print_success "All 21 agents tested successfully!"
}

# Usage information
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all                 Run all tests (default)"
    echo "  core                Run core agent tests (7 agents)"
    echo "  orchestrators       Run orchestrator tests (2 agents)"
    echo "  design-specialists  Run design review specialist tests (6 agents)"
    echo "  code-specialists    Run code review specialist tests (6 agents)"
    echo "  integration         Run integration/E2E tests"
    echo "  performance         Run performance tests"
    echo "  unit                Run all unit tests"
    echo "  e2e                 Run all E2E tests"
    echo "  coverage            Run all tests with coverage report"
    echo "  incremental         Run all tests incrementally (recommended)"
    echo "  help                Show this help message"
    echo ""
    echo "Options:"
    echo "  VERBOSE=1           Show full pytest output (default: summary only)"
    echo "  LOG_DIR=<path>      Directory for log files (default: /tmp/agent_test_logs)"
    echo ""
    echo "Output Modes (context-efficient backpressure):"
    echo "  Default: Shows pass/fail summary, full output only on failure"
    echo "  VERBOSE=1: Streams all pytest output in real-time"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run all tests, summary output"
    echo "  VERBOSE=1 $0 all          # Run all tests, full output"
    echo "  $0 core                   # Test only core agents"
    echo "  $0 incremental            # Run tests phase by phase"
    echo "  $0 coverage               # Run with coverage report"
    echo "  LOG_DIR=./logs $0 unit    # Custom log directory"
}

# Main execution
main() {
    # Parse command first (help doesn't need env check)
    command=${1:-all}

    if [ "$command" = "help" ] || [ "$command" = "--help" ] || [ "$command" = "-h" ]; then
        usage
        exit 0
    fi

    # Check environment for actual test runs
    check_env_vars

    case $command in
        all)
            run_all_tests
            ;;
        core)
            run_core_agents
            ;;
        orchestrators)
            run_orchestrators
            ;;
        design-specialists)
            run_design_specialists
            ;;
        code-specialists)
            run_code_specialists
            ;;
        integration)
            run_integration_tests
            ;;
        performance)
            run_performance_tests
            ;;
        unit)
            run_unit_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        coverage)
            run_with_coverage
            ;;
        incremental)
            run_incremental
            ;;
        *)
            print_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac

    print_header "Test Execution Complete"
    print_success "All requested tests completed successfully!"
}

# Run main function
main "$@"
