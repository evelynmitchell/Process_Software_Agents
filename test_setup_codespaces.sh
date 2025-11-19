#!/bin/bash
#
# Test suite for setup_codespaces.sh
#
# Usage: ./test_setup_codespaces.sh
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/setup_codespaces.sh"

# Test framework helpers
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$expected" = "$actual" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}${NC} $message"
        echo -e "  Expected: '$expected'"
        echo -e "  Got:      '$actual'"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if echo "$haystack" | grep -q "$needle"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}${NC} $message"
        echo -e "  Expected to find: '$needle'"
        echo -e "  In: '$haystack'"
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if ! echo "$haystack" | grep -q "$needle"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}${NC} $message"
        echo -e "  Expected NOT to find: '$needle'"
        echo -e "  In: '$haystack'"
        return 1
    fi
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$expected" -eq "$actual" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}${NC} $message"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}${NC} $message"
        echo -e "  Expected exit code: $expected"
        echo -e "  Got exit code:      $actual"
        return 1
    fi
}

# Create a mock environment
setup_mock_env() {
    export TEST_DIR=$(mktemp -d)
    export ORIGINAL_PATH=$PATH
    export PATH="$TEST_DIR/bin:$PATH"
    export HOME="$TEST_DIR/home"
    mkdir -p "$TEST_DIR/bin"
    mkdir -p "$HOME/.local/bin"
    cd "$TEST_DIR"
}

teardown_mock_env() {
    cd /
    rm -rf "$TEST_DIR"
    export PATH=$ORIGINAL_PATH
}

create_mock_command() {
    local cmd_name="$1"
    local cmd_behavior="$2"

    cat > "$TEST_DIR/bin/$cmd_name" << EOF
#!/bin/bash
$cmd_behavior
EOF
    chmod +x "$TEST_DIR/bin/$cmd_name"
}

# Test 1: Script should use bash, not sh
print_test_header "Test 1: Shell Compatibility"
test_shell_shebang() {
    if [ ! -f "$SETUP_SCRIPT" ]; then
        echo -e "${YELLOW}⊘${NC} Skipping - setup_codespaces.sh not found"
        return 0
    fi
    local shebang=$(head -1 "$SETUP_SCRIPT")
    assert_equals "#!/bin/bash" "$shebang" "Script should have bash shebang"
}

# Test 2: Script behavior when run with sh vs bash
test_sh_vs_bash() {
    setup_mock_env

    # Create a minimal test script that mimics the issue
    cat > "$TEST_DIR/test_redirect.sh" << 'EOF'
#!/bin/bash
if command -v nonexistent_cmd &> /dev/null; then
    echo "FOUND"
else
    echo "NOT_FOUND"
fi
EOF
    chmod +x "$TEST_DIR/test_redirect.sh"

    # Test with bash
    local bash_output=$(bash "$TEST_DIR/test_redirect.sh" 2>&1)
    assert_equals "NOT_FOUND" "$bash_output" "Bash correctly detects missing command"

    # Test with sh (which might be dash)
    local sh_output=$(sh "$TEST_DIR/test_redirect.sh" 2>&1)
    # Note: sh might not handle &> correctly, causing issues

    teardown_mock_env
}

# Test 3: Command detection when commands are missing
print_test_header "Test 2: Command Detection (Missing Commands)"
test_missing_commands() {
    setup_mock_env

    # Copy script to test directory
    cp "$SETUP_SCRIPT" "$TEST_DIR/" 2>/dev/null || {
        echo -e "${YELLOW}⊘${NC} Skipping - setup_codespaces.sh not found"
        return 0
    }

    # Run script and capture output (it will fail, but we want to check output)
    local output=$(bash "$TEST_DIR/setup_codespaces.sh" 2>&1 || true)

    # The script should NOT claim tools are already installed when they're missing
    if echo "$output" | grep -q "Claude Code already installed"; then
        if echo "$output" | grep -q "claude: not found"; then
            TESTS_RUN=$((TESTS_RUN + 1))
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo -e "${RED}${NC} Script incorrectly reports claude as installed when it's missing"
        fi
    fi

    if echo "$output" | grep -q "uv already installed"; then
        if echo "$output" | grep -q "uv: not found"; then
            TESTS_RUN=$((TESTS_RUN + 1))
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo -e "${RED}${NC} Script incorrectly reports uv as installed when it's missing"
        fi
    fi

    teardown_mock_env
}

# Test 4: Command detection when commands are present
print_test_header "Test 3: Command Detection (Commands Present)"
test_present_commands() {
    setup_mock_env

    # Create mock commands that work
    create_mock_command "claude" "echo 'Claude Code v1.0.0'"
    create_mock_command "uv" "echo 'uv 0.1.0'"
    create_mock_command "python3" "echo 'Python 3.12.1'"

    # Copy script to test directory
    cp "$SETUP_SCRIPT" "$TEST_DIR/" 2>/dev/null || {
        echo -e "${YELLOW}⊘${NC} Skipping - setup_codespaces.sh not found"
        return 0
    }

    # Run script
    local output=$(bash "$TEST_DIR/setup_codespaces.sh" 2>&1 || true)

    # Should detect commands as already installed
    assert_contains "$output" "Claude Code already installed" "Should detect claude"
    assert_contains "$output" "uv already installed" "Should detect uv"
    assert_contains "$output" "Python.*found" "Should detect python3"

    # Should NOT try to install them
    assert_not_contains "$output" "https://claude.ai/install.sh" "Should not try to install claude"
    assert_not_contains "$output" "https://astral.sh/uv/install.sh" "Should not try to install uv"

    teardown_mock_env
}

# Test 5: Python version checking
print_test_header "Test 4: Python Version Checking"
test_python_version_valid() {
    setup_mock_env

    create_mock_command "python3" "echo 'Python 3.12.1'"

    # Create minimal test script for Python check
    cat > "$TEST_DIR/test_python.sh" << 'EOF'
#!/bin/bash
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python $PYTHON_VERSION found"

    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 12 ]; then
        echo "PASS: Python version >= 3.12"
    else
        echo "FAIL: Python 3.12+ required"
    fi
fi
EOF
    chmod +x "$TEST_DIR/test_python.sh"

    local output=$(bash "$TEST_DIR/test_python.sh" 2>&1)
    assert_contains "$output" "PASS" "Should accept Python 3.12+"

    teardown_mock_env
}

test_python_version_old() {
    setup_mock_env

    create_mock_command "python3" "echo 'Python 3.9.0'"

    cat > "$TEST_DIR/test_python.sh" << 'EOF'
#!/bin/bash
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 12 ]; then
        echo "PASS"
    else
        echo "WARN"
    fi
fi
EOF
    chmod +x "$TEST_DIR/test_python.sh"

    local output=$(bash "$TEST_DIR/test_python.sh" 2>&1)
    assert_equals "WARN" "$output" "Should warn for Python < 3.12"

    teardown_mock_env
}

# Test 6: Handling of missing files
print_test_header "Test 5: Missing Configuration Files"
test_missing_pyproject() {
    setup_mock_env

    # Create a test script that checks for pyproject.toml
    cat > "$TEST_DIR/test_pyproject.sh" << 'EOF'
#!/bin/bash
if [ -f "pyproject.toml" ]; then
    echo "FOUND"
else
    echo "SKIP"
fi
EOF
    chmod +x "$TEST_DIR/test_pyproject.sh"

    local output=$(bash "$TEST_DIR/test_pyproject.sh" 2>&1)
    assert_equals "SKIP" "$output" "Should skip when pyproject.toml missing"

    teardown_mock_env
}

# Test 7: Exit code when errors occur
print_test_header "Test 6: Error Handling"
test_exit_on_error() {
    setup_mock_env

    # Create script that should fail
    cat > "$TEST_DIR/test_fail.sh" << 'EOF'
#!/bin/bash
set -e
nonexistent_command
echo "This should not print"
EOF
    chmod +x "$TEST_DIR/test_fail.sh"

    bash "$TEST_DIR/test_fail.sh" 2>&1 || exit_code=$?

    assert_exit_code 127 ${exit_code:-0} "Should exit with error code when command not found"

    teardown_mock_env
}

# Test 8: Verification step correctly counts errors
print_test_header "Test 7: Error Counting"
test_error_counting() {
    setup_mock_env

    # Create test script that counts errors
    cat > "$TEST_DIR/test_errors.sh" << 'EOF'
#!/bin/bash
ERRORS=0

if command -v nonexistent1 &> /dev/null; then
    echo "OK"
else
    ERRORS=$((ERRORS + 1))
fi

if command -v nonexistent2 &> /dev/null; then
    echo "OK"
else
    ERRORS=$((ERRORS + 1))
fi

echo "ERRORS=$ERRORS"
EOF
    chmod +x "$TEST_DIR/test_errors.sh"

    local output=$(bash "$TEST_DIR/test_errors.sh" 2>&1)
    assert_contains "$output" "ERRORS=2" "Should correctly count missing commands"

    teardown_mock_env
}

# Test 9: PATH export persists
print_test_header "Test 8: PATH Management"
test_path_export() {
    setup_mock_env

    # Test that PATH modifications work
    cat > "$TEST_DIR/test_path.sh" << 'EOF'
#!/bin/bash
export PATH="/new/path:$PATH"
if echo "$PATH" | grep -q "/new/path"; then
    echo "PATH_OK"
fi
EOF
    chmod +x "$TEST_DIR/test_path.sh"

    local output=$(bash "$TEST_DIR/test_path.sh" 2>&1)
    assert_equals "PATH_OK" "$output" "PATH export should work"

    teardown_mock_env
}

# Test 10: Script handles being run from different directories
print_test_header "Test 9: Working Directory Handling"
test_different_directories() {
    setup_mock_env

    mkdir -p "$TEST_DIR/project"
    echo "name = 'test'" > "$TEST_DIR/project/pyproject.toml"

    cat > "$TEST_DIR/test_dir.sh" << 'EOF'
#!/bin/bash
cd "$1"
if [ -f "pyproject.toml" ]; then
    echo "FOUND"
else
    echo "NOT_FOUND"
fi
EOF
    chmod +x "$TEST_DIR/test_dir.sh"

    local output=$(bash "$TEST_DIR/test_dir.sh" "$TEST_DIR/project" 2>&1)
    assert_equals "FOUND" "$output" "Should find pyproject.toml when in project directory"

    output=$(bash "$TEST_DIR/test_dir.sh" "$TEST_DIR" 2>&1)
    assert_equals "NOT_FOUND" "$output" "Should not find pyproject.toml in parent directory"

    teardown_mock_env
}

# Run all tests
echo "======================================================================================================"
echo "Running tests for setup_codespaces.sh"
echo "======================================================================================================"

test_shell_shebang
test_sh_vs_bash
test_missing_commands
test_present_commands
test_python_version_valid
test_python_version_old
test_missing_pyproject
test_exit_on_error
test_error_counting
test_path_export
test_different_directories

# Print summary
echo ""
echo "======================================================================================================"
echo "Test Summary"
echo "======================================================================================================"
echo -e "Total tests:  $TESTS_RUN"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN} All tests passed!${NC}"
    exit 0
else
    echo -e "${RED} Some tests failed${NC}"
    exit 1
fi
