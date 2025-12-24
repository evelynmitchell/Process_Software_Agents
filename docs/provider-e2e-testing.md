# Provider E2E Testing Guide

This document describes how to set up and run end-to-end tests for LLM providers.

## Overview

The provider e2e tests verify actual API connectivity and response handling for:
- **Anthropic** (Claude models)
- **OpenRouter** (100+ models including Claude, GPT-4, Llama)
- **Groq** (Ultra-fast LPU inference)

Tests are designed to:
- Skip automatically when API keys are not available
- Use minimal token counts to reduce costs
- Validate response structure and error handling

## Running Tests Locally

### Without API Keys (Mock Mode)
Tests skip gracefully when API keys are not set:

```bash
# All provider tests will be skipped
pytest tests/e2e/test_providers_e2e.py -v
```

### With API Keys
Set environment variables and run:

```bash
# Set one or more API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."
export GROQ_API_KEY="gsk_..."

# Run all provider tests
pytest tests/e2e/test_providers_e2e.py -v -s

# Run tests for a specific provider
pytest tests/e2e/test_providers_e2e.py -v -s -k "anthropic"
pytest tests/e2e/test_providers_e2e.py -v -s -k "openrouter"
pytest tests/e2e/test_providers_e2e.py -v -s -k "groq"
```

## GitHub Actions Setup

### Step 1: Add Repository Secrets

Go to your repository's **Settings > Secrets and variables > Actions** and add:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key (starts with `sk-ant-`) | Recommended |
| `OPENROUTER_API_KEY` | OpenRouter API key | Optional |
| `GROQ_API_KEY` | Groq API key (starts with `gsk_`) | Optional |

### Step 2: Workflow Triggers

The provider e2e workflow (`.github/workflows/provider-e2e.yml`) runs:

1. **Manually** - Via "Actions" tab > "Provider E2E Tests" > "Run workflow"
2. **On push to main** - When provider code changes
3. **Weekly** - Every Sunday at 2am UTC (catches API changes)

### Step 3: Verify Setup

After adding secrets:
1. Go to Actions tab
2. Select "Provider E2E Tests"
3. Click "Run workflow"
4. Check the summary for which providers were tested

## Cost Considerations

The tests are designed to minimize API costs:

| Provider | Model Used | Tokens per Test | Est. Cost per Run |
|----------|------------|-----------------|-------------------|
| Anthropic | claude-haiku-4-5 | ~20 | < $0.001 |
| OpenRouter | claude-3.5-haiku | ~20 | < $0.001 |
| Groq | llama-3.1-8b-instant | ~20 | < $0.001 |

**Total estimated cost per full test run: < $0.01**

## Test Structure

```
tests/e2e/test_providers_e2e.py
├── TestAnthropicProviderE2E
│   ├── test_basic_call_sync
│   ├── test_basic_call_async
│   ├── test_json_response_parsing
│   ├── test_available_models
│   ├── test_cost_estimation
│   └── test_invalid_api_key_raises_error
├── TestOpenRouterProviderE2E
│   ├── test_basic_call_sync
│   ├── test_basic_call_async
│   ├── test_available_models
│   ├── test_headers_include_referer
│   └── test_invalid_api_key_raises_error
├── TestGroqProviderE2E
│   ├── test_basic_call_sync
│   ├── test_basic_call_async
│   ├── test_ultra_fast_inference
│   ├── test_available_models
│   └── test_invalid_api_key_raises_error
├── TestProviderRegistryE2E
│   └── test_registry_lists_all_providers
└── TestCrossProviderE2E
    └── test_same_prompt_different_providers
```

## Adding Tests for New Providers

When adding a new provider (e.g., Gemini):

1. Add skip condition:
```python
HAS_GEMINI_KEY = bool(os.getenv("GOOGLE_API_KEY"))

skip_without_gemini = pytest.mark.skipif(
    not HAS_GEMINI_KEY,
    reason="GOOGLE_API_KEY not set - skipping Gemini e2e tests"
)
```

2. Add test class:
```python
@pytest.mark.e2e
@pytest.mark.provider
class TestGeminiProviderE2E:
    @skip_without_gemini
    def test_basic_call_sync(self, minimal_prompt):
        # ...
```

3. Add secret to GitHub Actions
4. Update workflow env vars

## Troubleshooting

### Tests Skipped Unexpectedly
- Check that environment variables are exported (not just set)
- Verify the API key format is correct
- Check for typos in secret names

### Authentication Errors
- Verify API key is valid and not expired
- Check account has sufficient credits/quota
- Ensure API key has required permissions

### Rate Limit Errors
- Wait and retry (tests use minimal requests)
- Check provider dashboard for quota status
- Consider running tests sequentially: `pytest -v -s --workers 1`
