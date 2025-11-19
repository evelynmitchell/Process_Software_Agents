#!/bin/bash
# Test Execution Script for All 21 Agents
# Based on Comprehensive Agent Test Plan v1.0.0

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install dependencies: pip install -e \".[dev]\""
    exit 1
fi

# Check environment variables
check_env_vars() {
    print_header "Checking Environment Variables"

    missing_vars=()

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        missing_vars+=("ANTHROPIC_API_KEY")
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        missing_vars+=("OPENAI_API_KEY")
    fi

    if [ -z "$LANGFUSE_PUBLIC_KEY" ]; then
        missing_vars+=("LANGFUSE_PUBLIC_KEY")
    fi

    if [ -z "$LANGFUSE_SECRET_KEY" ]; then
        missing_vars+=("LANGFUSE_SECRET_KEY")
    fi

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing environment variables: ${missing_vars[*]}"
        print_info "Please set the following variables:"
        for var in "${missing_vars[@]}"; do
            echo "  export $var=\"your_key_here\""
        done
        exit 1
    else
        print_success "All environment variables set"
    fi
}

# Test suite functions
run_all_tests() {
    print_header "Running ALL Tests (21 Agents)"
    pytest tests/ -v --tb=short
}

run_core_agents() {
    print_header "Phase 1: Core Agents (7 Agents)"

    print_info "Testing Planning Agent (FR-1)..."
    pytest tests/unit/test_agents/test_planning_agent.py -v --tb=short
    pytest tests/e2e/test_planning_agent_e2e.py -v --tb=short
    print_success "Planning Agent tests passed"

    print_info "Testing Design Agent (FR-2)..."
    pytest tests/unit/test_agents/test_design_agent.py -v --tb=short
    pytest tests/e2e/test_design_agent_e2e.py -v --tb=short
    print_success "Design Agent tests passed"

    print_info "Testing Design Review Agent (FR-3)..."
    pytest tests/unit/test_agents/test_design_review_agent.py -v --tb=short
    pytest tests/e2e/test_design_review_agent_e2e.py -v --tb=short
    print_success "Design Review Agent tests passed"

    print_info "Testing Code Agent (FR-4)..."
    pytest tests/unit/test_agents/test_code_agent.py -v --tb=short
    pytest tests/e2e/test_code_agent_e2e.py -v --tb=short
    print_success "Code Agent tests passed"

    print_info "Testing Code Review Agent (FR-5)..."
    pytest tests/unit/test_agents/test_code_review_orchestrator.py -v --tb=short
    print_success "Code Review Agent tests passed"

    print_info "Testing Test Agent (FR-6)..."
    pytest tests/unit/test_agents/test_test_agent.py -v --tb=short
    print_success "Test Agent tests passed"

    print_info "Testing Postmortem Agent (FR-7)..."
    pytest tests/unit/test_agents/test_postmortem_agent.py -v --tb=short
    print_success "Postmortem Agent tests passed"

    print_success "All Core Agents tested successfully!"
}

run_orchestrators() {
    print_header "Phase 2: Orchestrator Agents (2 Agents)"

    print_info "Testing Design Review Orchestrator..."
    pytest tests/unit/test_agents/test_design_review_orchestrator.py -v --tb=short
    print_success "Design Review Orchestrator tests passed"

    print_info "Testing Code Review Orchestrator..."
    pytest tests/unit/test_agents/test_code_review_orchestrator.py -v --tb=short
    print_success "Code Review Orchestrator tests passed"

    print_success "All Orchestrator Agents tested successfully!"
}

run_design_specialists() {
    print_header "Phase 3: Design Review Specialists (6 Agents)"

    print_info "Testing all design review specialists..."
    pytest tests/unit/test_agents/reviews/ -v --tb=short

    print_success "All Design Review Specialists tested successfully!"
}

run_code_specialists() {
    print_header "Phase 4: Code Review Specialists (6 Agents)"

    print_info "Testing all code review specialists..."
    pytest tests/unit/test_agents/code_reviews/ -v --tb=short

    print_success "All Code Review Specialists tested successfully!"
}

run_integration_tests() {
    print_header "Phase 5: Integration & E2E Tests"

    print_info "Testing end-to-end workflows..."
    pytest tests/e2e/ -v --tb=short

    print_success "All integration tests passed successfully!"
}

run_performance_tests() {
    print_header "Phase 6: Performance Tests"

    if [ -d "tests/performance" ]; then
        print_info "Testing agent performance..."
        pytest tests/performance/ -v --tb=short
        print_success "Performance tests passed successfully!"
    else
        print_info "No performance tests found (tests/performance/ doesn't exist)"
    fi
}

run_unit_tests() {
    print_header "Running Unit Tests Only"
    pytest tests/unit/ -v --tb=short
}

run_e2e_tests() {
    print_header "Running E2E Tests Only"
    pytest tests/e2e/ -v --tb=short
}

run_with_coverage() {
    print_header "Running All Tests with Coverage Report"
    pytest tests/ -v --cov=src/asp --cov-report=html --cov-report=term --tb=short
    print_success "Coverage report generated in htmlcov/index.html"
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
    echo "Examples:"
    echo "  $0 all              # Run all tests"
    echo "  $0 core             # Test only core agents"
    echo "  $0 incremental      # Run tests phase by phase"
    echo "  $0 coverage         # Run with coverage report"
}

# Main execution
main() {
    # Check environment first
    check_env_vars

    # Parse command
    command=${1:-all}

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
        help)
            usage
            exit 0
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
