#!/bin/bash
# Script to initialize a local git repository for test artifacts
# This creates a separate repository to prevent polluting the main repo during testing

set -e  # Exit on error

# Configuration
REPO_DIR="test_artifacts_repo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_REPO_PATH="$PROJECT_ROOT/$REPO_DIR"

echo "=== Initializing Test Artifacts Repository ==="
echo "Location: $TEST_REPO_PATH"
echo ""

# Check if repository already exists
if [ -d "$TEST_REPO_PATH/.git" ]; then
    echo "⚠️  Test artifacts repository already exists at $TEST_REPO_PATH"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing repository..."
        rm -rf "$TEST_REPO_PATH"
    else
        echo "Keeping existing repository. Exiting."
        exit 0
    fi
fi

# Create the directory
echo "Creating directory: $TEST_REPO_PATH"
mkdir -p "$TEST_REPO_PATH"

# Initialize git repository
cd "$TEST_REPO_PATH"
echo "Initializing git repository..."
git init

# Create initial structure
echo "Creating directory structure..."
mkdir -p artifacts
mkdir -p data
mkdir -p logs
mkdir -p temp

# Create README
cat > README.md << 'EOF'
# Test Artifacts Repository

This is a **local-only** git repository for testing and development purposes.

## Purpose

This repository is used to:
- Test agent workflows without polluting the main repository
- Store temporary artifacts during development
- Experiment with git operations safely
- Validate automation scripts

## Structure

```
test_artifacts_repo/
├── artifacts/     # Agent-generated artifacts (designs, code, tests)
├── data/          # Test data files
├── logs/          # Log files from test runs
├── temp/          # Temporary files
└── README.md      # This file
```

## Usage

This repository is automatically created by `scripts/init_test_artifacts_repo.sh`.

To recreate it from scratch:
```bash
cd /path/to/Process_Software_Agents
./scripts/init_test_artifacts_repo.sh
```

## Important Notes

⚠️ **This repository is NOT tracked by the main repository's git**

- All contents are excluded via `.gitignore`
- No commits here will affect the main repository
- Safe to delete and recreate at any time
- DO NOT commit sensitive information here

## Cleanup

To remove this repository:
```bash
cd /path/to/Process_Software_Agents
./scripts/cleanup_test_artifacts_repo.sh
```

Or manually:
```bash
rm -rf test_artifacts_repo
```
EOF

# Create .gitignore for the test repo
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyc
.pytest_cache/

# Logs
*.log
logs/

# Temp files
*.tmp
*.temp
temp/

# OS files
.DS_Store
Thumbs.db
*~
EOF

# Create initial commit
echo "Creating initial commit..."
git add .
git commit -m "Initial commit: Test artifacts repository structure"

# Create a test branch
git checkout -b test-main

echo ""
echo "✅ Test artifacts repository successfully initialized!"
echo ""
echo "Repository location: $TEST_REPO_PATH"
echo "Current branch: $(git branch --show-current)"
echo ""
echo "You can now use this repository for testing without affecting the main repo."
echo ""
echo "Example usage:"
echo "  cd $TEST_REPO_PATH"
echo "  # Run your tests here"
echo "  git status"
echo ""
