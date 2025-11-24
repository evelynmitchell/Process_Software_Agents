# Test Artifacts Repository Usage Guide

## Overview

The Test Artifacts Repository is a **local-only git repository** created specifically for testing agent workflows, validating automation scripts, and experimenting with git operations without affecting the main Process_Software_Agents repository.

## Purpose

This isolated repository allows you to:

1. **Safe Testing**: Run agent workflows without risk of polluting the main repository
2. **Artifact Validation**: Test artifact generation in a clean environment
3. **Git Operations**: Experiment with git commands safely
4. **Development Iteration**: Quickly iterate on features without cluttering git history

## Quick Start

### Initialize the Test Repository

```bash
# From the Process_Software_Agents root directory
./scripts/init_test_artifacts_repo.sh
```

This creates a new git repository at `test_artifacts_repo/` with:
- Initial directory structure (artifacts/, data/, logs/, temp/)
- README explaining the repository purpose
- Initial git commit
- A `test-main` branch ready for use

### Using the Test Repository

```bash
# Navigate to the test repository
cd test_artifacts_repo

# Check status
git status

# Create test files
echo "Test content" > artifacts/test.txt
git add artifacts/test.txt
git commit -m "Test commit"

# Verify isolation - changes here don't affect main repo
cd ..
git status  # test_artifacts_repo/ won't appear (excluded by .gitignore)
```

### Cleanup

```bash
# From the Process_Software_Agents root directory
./scripts/cleanup_test_artifacts_repo.sh
```

This permanently removes the test repository. You can recreate it anytime with the init script.

## Scripts Reference

### `init_test_artifacts_repo.sh`

**Location**: `scripts/init_test_artifacts_repo.sh`

**Purpose**: Creates and initializes the test artifacts repository

**Features**:
- Checks if repository already exists
- Prompts before overwriting existing repository
- Creates standard directory structure
- Initializes git with an initial commit
- Creates a `test-main` branch

**Usage**:
```bash
./scripts/init_test_artifacts_repo.sh
```

**Output**:
- New repository at `test_artifacts_repo/`
- Initial commit with README and .gitignore
- Clean working tree on `test-main` branch

---

### `cleanup_test_artifacts_repo.sh`

**Location**: `scripts/cleanup_test_artifacts_repo.sh`

**Purpose**: Safely removes the test artifacts repository

**Features**:
- Checks if repository exists
- Shows size of directory to be deleted
- Requires confirmation before deletion
- Completely removes the directory

**Usage**:
```bash
./scripts/cleanup_test_artifacts_repo.sh
```

**Safety**:
- Prompts for confirmation
- Shows what will be deleted
- Provides feedback on completion

## Repository Structure

```
test_artifacts_repo/
├── .git/              # Git metadata (separate from main repo)
├── .gitignore         # Ignores common temp files, logs, etc.
├── README.md          # Repository documentation
├── artifacts/         # For agent-generated artifacts
├── data/              # For test data files
├── logs/              # For log files
└── temp/              # For temporary files
```

## Use Cases

### 1. Testing Agent Workflows

```bash
# Initialize test repo
./scripts/init_test_artifacts_repo.sh

# Set environment to use test repo
export ARTIFACT_PATH="$PWD/test_artifacts_repo/artifacts"

# Run your agent tests
python -m pytest tests/test_agent_workflow.py

# Review generated artifacts
ls -la test_artifacts_repo/artifacts/

# Clean up when done
./scripts/cleanup_test_artifacts_repo.sh
```

### 2. Validating Git Operations

```bash
cd test_artifacts_repo

# Test git operations safely
git checkout -b feature-test
echo "new feature" > artifacts/feature.txt
git add artifacts/feature.txt
git commit -m "Add feature"
git log --oneline

# Experiment with merges, rebases, etc.
git checkout test-main
git merge feature-test
```

### 3. Agent Artifact Generation Testing

```bash
# Use test repo for artifact output
cd test_artifacts_repo

# Run agent (example)
python /home/user/Process_Software_Agents/src/agents/design_agent.py \
  --task-id TEST-001 \
  --output-dir ./artifacts

# Verify artifacts
git status
git add artifacts/TEST-001/
git commit -m "Test: Design Agent artifacts for TEST-001"
```

## Important Notes

⚠️ **Isolation**: The test repository is completely separate from the main repository:
- Different `.git` directory
- Separate commit history
- Excluded from main repo via `.gitignore`
- No remote configured (local only)

✅ **Safety**: Safe to delete and recreate:
- No risk to main repository
- Can recreate identical structure anytime
- Useful for clean-slate testing

🔒 **Privacy**:
- Not tracked by version control
- Won't be pushed to remote
- Local development only

## Troubleshooting

### Repository Already Exists

If you see "Test artifacts repository already exists", you have two options:

1. **Keep existing**: Answer "N" to preserve current test data
2. **Recreate**: Answer "Y" to start fresh

### Permission Issues

If scripts aren't executable:

```bash
chmod +x scripts/init_test_artifacts_repo.sh
chmod +x scripts/cleanup_test_artifacts_repo.sh
```

### Repository Not Created

Verify you're in the correct directory:

```bash
pwd  # Should show: /home/user/Process_Software_Agents
./scripts/init_test_artifacts_repo.sh
```

## Integration with Testing

### Pytest Configuration

You can configure pytest to use the test repository:

```python
# conftest.py
import pytest
import os

@pytest.fixture
def test_repo_path():
    """Provide path to test artifacts repository."""
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "test_artifacts_repo")

@pytest.fixture
def test_artifacts_dir(test_repo_path):
    """Provide path to test artifacts directory."""
    return os.path.join(test_repo_path, "artifacts")
```

### Environment Variables

```bash
# Set environment for tests to use test repo
export TEST_ARTIFACT_REPO="/home/user/Process_Software_Agents/test_artifacts_repo"
export TEST_ARTIFACT_DIR="$TEST_ARTIFACT_REPO/artifacts"

# Run tests
pytest tests/
```

## Best Practices

1. **Clean Slate**: Run `cleanup` and `init` scripts between major test sessions
2. **Commit Often**: Use git commits to mark test milestones
3. **Branch Strategy**: Create branches for different test scenarios
4. **Documentation**: Add notes in the test repo's README for complex test setups
5. **Isolation**: Never configure a git remote for this repository

## Related Documentation

- [Agent Development Guide](./api_documentation.md)
- [Test Plan](./comprehensive_agent_test_plan.md)
- [Artifact Persistence](./artifact_persistence_user_guide.md)

## Maintenance

### Regular Cleanup

Consider cleaning up the test repository periodically:

```bash
# Check size
du -sh test_artifacts_repo

# If large, clean up
./scripts/cleanup_test_artifacts_repo.sh
./scripts/init_test_artifacts_repo.sh
```

### Script Updates

Both scripts are located in `scripts/` and can be modified as needed. Key sections:

- **REPO_DIR**: Change if you want a different directory name
- **Directory structure**: Modify the `mkdir -p` commands in init script
- **Initial files**: Update the heredoc sections for README and .gitignore

---

**Created**: 2025-11-23
**Session**: 20251123.2
**Purpose**: Testing infrastructure for safe agent workflow development
