#!/bin/bash
# E2E Pipeline Test Script
# Runs the full TSP Orchestrator pipeline with various test scenarios

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/e2e_results}"
DB_PATH="${DB_PATH:-data/asp_telemetry.db}"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Test scenarios
declare -A SCENARIOS
SCENARIOS["calculator"]="Create a simple calculator module with add, subtract, multiply, divide functions. Include input validation and error handling for division by zero."
SCENARIOS["todo"]="Create a todo list application with add, remove, list, and mark-complete functions. Store todos in memory with unique IDs."
SCENARIOS["validator"]="Create an email validator module that checks format, domain, and provides helpful error messages."
SCENARIOS["logger"]="Create a simple logging utility with log levels (debug, info, warn, error), timestamps, and file output support."

# Functions
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_phase() {
    echo -e "${CYAN}▶ $1${NC}"
}

check_requirements() {
    print_header "Checking Requirements"

    # Check uv
    if ! command -v uv &> /dev/null; then
        print_error "uv not found. Please install uv first."
        exit 1
    fi
    print_success "uv found"

    # Check ANTHROPIC_API_KEY
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_error "ANTHROPIC_API_KEY not set"
        print_info "Set it with: export ANTHROPIC_API_KEY='your-key'"
        exit 1
    fi
    print_success "ANTHROPIC_API_KEY set"

    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    print_success "Output directory: $OUTPUT_DIR"
}

run_pipeline() {
    local task_id="$1"
    local description="$2"
    local output_file="$3"
    local mode="${4:-auto-approve}"
    local verbose="${VERBOSE:-0}"

    print_phase "Running pipeline: $task_id"
    echo -e "  Description: ${description:0:60}..."
    echo -e "  Output: $output_file"
    echo ""

    local start_time=$(date +%s)
    local exit_code=0
    local log_file="${output_file%.json}.log"

    # Build command based on mode
    local cmd="uv run python -m asp.cli run --task-id \"$task_id\" --description \"$description\" -o \"$output_file\""

    case $mode in
        auto-approve)
            cmd="$cmd --auto-approve"
            ;;
        hitl)
            cmd="$cmd --hitl-database"
            ;;
        strict)
            # No flags - quality gate failures will halt pipeline
            ;;
    esac

    if [ -n "$DB_PATH" ]; then
        cmd="$cmd --db-path \"$DB_PATH\""
    fi

    # Context-efficient backpressure pattern:
    # - On success: show only summary (suppress verbose output)
    # - On failure: show full log for debugging
    # Reference: https://www.hlyr.dev/blog/context-efficient-backpressure

    if [ "$verbose" = "1" ]; then
        # Verbose mode: stream everything
        if eval "$cmd" 2>&1 | tee "$log_file"; then
            exit_code=0
        else
            exit_code=$?
        fi
    else
        # Quiet mode: capture output, show summary
        echo -e "  ${YELLOW}Running (output captured to log)...${NC}"

        # Show progress indicators by filtering for phase markers
        if eval "$cmd" 2>&1 | tee "$log_file" | grep --line-buffered -E "^\[PHASE|EXECUTION COMPLETE|Overall Status|Duration:|Files Generated:|Tests Passed:|✓|✗"; then
            exit_code=0
        else
            exit_code=${PIPESTATUS[0]}
        fi
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $exit_code -eq 0 ]; then
        print_success "Pipeline completed in ${duration}s"
        # Show brief summary from result file
        if [ -f "$output_file" ]; then
            local status=$(jq -r '.overall_status // "?"' "$output_file" 2>/dev/null)
            local files=$(jq -r '.generated_code.total_files // "?"' "$output_file" 2>/dev/null)
            echo -e "  Status: ${GREEN}$status${NC}, Files: $files"
        fi
    else
        print_error "Pipeline failed (exit code: $exit_code) after ${duration}s"
        # On failure, show the tail of the log for debugging
        echo ""
        echo -e "${RED}═══ Last 30 lines of log ═══${NC}"
        tail -30 "$log_file"
        echo -e "${RED}═══ Full log: $log_file ═══${NC}"
    fi

    return $exit_code
}

run_scenario() {
    local scenario="$1"
    local description="${SCENARIOS[$scenario]}"

    if [ -z "$description" ]; then
        print_error "Unknown scenario: $scenario"
        print_info "Available scenarios: ${!SCENARIOS[*]}"
        return 1
    fi

    local task_id="E2E-${scenario^^}-$TIMESTAMP"
    local output_file="$OUTPUT_DIR/${task_id}.json"

    run_pipeline "$task_id" "$description" "$output_file"
}

run_custom() {
    local description="$1"
    local task_id="E2E-CUSTOM-$TIMESTAMP"
    local output_file="$OUTPUT_DIR/${task_id}.json"

    run_pipeline "$task_id" "$description" "$output_file"
}

run_all_scenarios() {
    print_header "Running All Test Scenarios"

    local passed=0
    local failed=0
    local results=()

    for scenario in "${!SCENARIOS[@]}"; do
        echo ""
        print_info "Scenario: $scenario"

        if run_scenario "$scenario"; then
            ((passed++))
            results+=("✓ $scenario")
        else
            ((failed++))
            results+=("✗ $scenario")
        fi
    done

    print_header "Test Summary"
    for result in "${results[@]}"; do
        if [[ $result == "✓"* ]]; then
            echo -e "${GREEN}$result${NC}"
        else
            echo -e "${RED}$result${NC}"
        fi
    done

    echo ""
    echo -e "Passed: ${GREEN}$passed${NC}"
    echo -e "Failed: ${RED}$failed${NC}"
    echo -e "Total:  $((passed + failed))"

    [ $failed -eq 0 ]
}

run_quick() {
    print_header "Quick E2E Test (Calculator)"
    run_scenario "calculator"
}

show_results() {
    print_header "Recent E2E Results"

    if [ -d "$OUTPUT_DIR" ]; then
        local files=$(ls -t "$OUTPUT_DIR"/*.json 2>/dev/null | head -10)
        if [ -n "$files" ]; then
            for f in $files; do
                local basename=$(basename "$f" .json)
                local status=$(jq -r '.overall_status // "UNKNOWN"' "$f" 2>/dev/null || echo "PARSE_ERROR")
                local duration=$(jq -r '.total_duration_seconds // 0' "$f" 2>/dev/null || echo "?")
                local files_gen=$(jq -r '.generated_code.total_files // 0' "$f" 2>/dev/null || echo "?")

                case $status in
                    PASS|CONDITIONAL_PASS)
                        echo -e "${GREEN}✓${NC} $basename - ${status} (${duration}s, ${files_gen} files)"
                        ;;
                    FAIL)
                        echo -e "${RED}✗${NC} $basename - ${status} (${duration}s)"
                        ;;
                    *)
                        echo -e "${YELLOW}?${NC} $basename - ${status}"
                        ;;
                esac
            done
        else
            print_info "No results found in $OUTPUT_DIR"
        fi
    else
        print_info "Output directory doesn't exist: $OUTPUT_DIR"
    fi
}

show_status() {
    print_header "ASP Platform Status"
    uv run python -m asp.cli status ${DB_PATH:+--db-path "$DB_PATH"}
}

init_db() {
    print_header "Initializing Database"
    uv run python -m asp.cli init-db ${DB_PATH:+--db-path "$DB_PATH"} "$@"
}

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  quick               Run quick E2E test (calculator scenario)"
    echo "  scenario <name>     Run a specific scenario"
    echo "  custom \"<desc>\"     Run with custom task description"
    echo "  all                 Run all predefined scenarios"
    echo "  results             Show recent E2E results"
    echo "  status              Show ASP platform status"
    echo "  init-db [--reset]   Initialize/reset the database"
    echo "  help                Show this help"
    echo ""
    echo "Scenarios:"
    for scenario in "${!SCENARIOS[@]}"; do
        echo "  $scenario"
        echo "    ${SCENARIOS[$scenario]:0:70}..."
    done
    echo ""
    echo "Options:"
    echo "  OUTPUT_DIR=<path>   Output directory (default: /tmp/e2e_results)"
    echo "  DB_PATH=<path>      Database path (default: data/asp_telemetry.db)"
    echo "  VERBOSE=1           Show full output (default: summary only)"
    echo ""
    echo "Output Modes (context-efficient backpressure):"
    echo "  Default: Shows phase markers only, full log on failure"
    echo "  VERBOSE=1: Streams all output in real-time"
    echo ""
    echo "Examples:"
    echo "  $0 quick                              # Fast test, summary output"
    echo "  VERBOSE=1 $0 quick                    # Fast test, full output"
    echo "  $0 scenario calculator                # Run calculator scenario"
    echo "  $0 custom \"Build a REST API...\"       # Custom description"
    echo "  $0 all                                # Run all scenarios"
    echo "  OUTPUT_DIR=./results $0 quick         # Custom output dir"
}

# Main
main() {
    local command="${1:-help}"
    shift 2>/dev/null || true

    case $command in
        quick)
            check_requirements
            run_quick
            ;;
        scenario)
            check_requirements
            run_scenario "$1"
            ;;
        custom)
            check_requirements
            run_custom "$1"
            ;;
        all)
            check_requirements
            run_all_scenarios
            ;;
        results)
            show_results
            ;;
        status)
            show_status
            ;;
        init-db)
            init_db "$@"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            print_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
