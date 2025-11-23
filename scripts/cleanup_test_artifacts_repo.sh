#!/bin/bash
# Script to clean up the test artifacts repository
# This completely removes the test repository

set -e  # Exit on error

# Configuration
REPO_DIR="test_artifacts_repo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_REPO_PATH="$PROJECT_ROOT/$REPO_DIR"

echo "=== Cleanup Test Artifacts Repository ==="
echo "Target: $TEST_REPO_PATH"
echo ""

# Check if repository exists
if [ ! -d "$TEST_REPO_PATH" ]; then
    echo "ℹ️  No test artifacts repository found at $TEST_REPO_PATH"
    echo "Nothing to clean up."
    exit 0
fi

# Confirm deletion
echo "⚠️  This will permanently delete the test artifacts repository and all its contents."
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Show what will be deleted
echo ""
echo "Contents to be deleted:"
du -sh "$TEST_REPO_PATH"
echo ""

# Delete the repository
echo "Removing $TEST_REPO_PATH..."
rm -rf "$TEST_REPO_PATH"

echo ""
echo "✅ Test artifacts repository successfully removed!"
echo ""
echo "To recreate it, run:"
echo "  ./scripts/init_test_artifacts_repo.sh"
echo ""
