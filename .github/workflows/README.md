# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the ASP Platform.

## Workflows

### `ci.yml` - Continuous Integration

Runs on all pushes and pull requests to `main`/`master` branches.

**Jobs:**
- **Test**: Runs pytest with coverage (80% minimum)
  - Python 3.12
  - Uses `uv` for dependency management
  - Uploads coverage to Codecov

- **Lint**: Code quality checks
  - Black (formatting)
  - isort (import sorting)
  - Ruff (fast Python linter)
  - Pylint (static analysis)
  - mypy (type checking)

- **Security**: Security scanning
  - Bandit (security linter)
  - Safety (dependency vulnerability checks)

### `docs.yml` - Documentation Publishing

Runs when documentation files change or on manual trigger.

**Jobs:**
- **Build**: Builds MkDocs documentation
  - Uses Material theme
  - Includes API documentation via mkdocstrings
  - Validates all internal links

- **Deploy**: Publishes to GitHub Pages
  - Only runs on pushes to main/master
  - Deploys to `https://evelynmitchell.github.io/Process_Software_Agents/`

## Configuration

All tools are configured in `pyproject.toml`:
- Black: Line length 88, Python 3.12
- isort: Black-compatible profile
- Ruff: Modern, fast linter with sensible defaults
- mypy: Strict type checking
- Coverage: 80% minimum threshold

## Local Development

Run the same checks locally:

```bash
# Install dependencies with uv
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .

# Lint
ruff check .
pylint src/

# Type check
mypy src/

# Build docs
mkdocs serve
```

## Enabling GitHub Pages

To enable documentation publishing:

1. Go to repository Settings → Pages
2. Set Source to "GitHub Actions"
3. Merge changes to main/master branch
4. Docs will be available at the GitHub Pages URL

## Badges

Add these to your README.md:

```markdown
![CI](https://github.com/evelynmitchell/Process_Software_Agents/workflows/CI/badge.svg)
![Docs](https://github.com/evelynmitchell/Process_Software_Agents/workflows/Documentation/badge.svg)
[![codecov](https://codecov.io/gh/evelynmitchell/Process_Software_Agents/branch/main/graph/badge.svg)](https://codecov.io/gh/evelynmitchell/Process_Software_Agents)
```
