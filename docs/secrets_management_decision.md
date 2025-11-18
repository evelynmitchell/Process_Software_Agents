# Secrets Management Decision

**Date:** November 12, 2025
**Status:** Accepted
**Deciders:** Engineering Team
**Decision Type:** Security & Development Workflow

---

## Context and Problem Statement

The ASP Platform requires API keys for external services:
- **Langfuse:** Observability platform (public key, secret key, host URL)
- **Anthropic:** Claude API for LLM agents
- **OpenAI:** (Optional) GPT-4 API for multi-provider support

**Primary development environment:** GitHub Codespaces

**Question:** How should we securely manage API keys and secrets in a Codespaces-based development workflow?

---

## Decision Drivers

1. **Security:** Secrets must never be committed to git history
2. **Persistence:** Secrets must survive Codespace rebuilds
3. **Convenience:** Easy for developers to set up and use
4. **Team Sharing:** Secrets should be shareable across team members
5. **Auditability:** Track who has access to what secrets
6. **Revocability:** Easy to rotate keys without code changes

---

## Considered Options

### Option 1: .env File (Git-Ignored)
Store secrets in a `.env` file excluded by `.gitignore`.

**Pros:**
-  Simple, widely understood pattern
-  Works with popular libraries (python-dotenv)
-  Easy local development

**Cons:**
-  Lost on Codespace rebuild (ephemeral)
-  Manual setup required for each new Codespace
-  No team sharing mechanism
-  Risk of accidental commit if .gitignore fails
-  Each developer manages their own copy

### Option 2: Encrypted Secrets in Git (git-crypt/SOPS)
Encrypt secrets and commit encrypted files to git.

**Pros:**
-  Secrets persist in git
-  Version controlled
-  Team sharing via git

**Cons:**
-  Complex setup (encryption keys, GPG)
-  Additional tooling required
-  Key distribution problem (how to share encryption keys?)
-  Secrets visible in git history (even if encrypted)
-  Difficult key rotation

### Option 3: GitHub Codespaces Secrets ⭐ **SELECTED**
Use GitHub's built-in Codespaces secrets management.

**Pros:**
-  **Native Codespaces integration** - automatically injected as environment variables
-  **Persistent** - survives Codespace rebuilds
-  **Encrypted** - stored securely by GitHub
-  **Auditable** - GitHub tracks access and changes
-  **Easy rotation** - update in GitHub UI, no code changes
-  **Team sharing** - repository-level or organization-level secrets
-  **Zero risk of git commit** - never touches local filesystem
-  **No additional tooling** - works out of the box

**Cons:**
-  GitHub-specific (not portable to other platforms)
-  Requires GitHub repo admin access to set up

### Option 4: Cloud Secret Manager (AWS Secrets Manager, HashiCorp Vault)
Use enterprise secret management service.

**Pros:**
-  Enterprise-grade security
-  Advanced features (rotation, audit logs)
-  Platform-agnostic

**Cons:**
-  Overkill for project size
-  Additional cost
-  Complex setup
-  Requires network access to secret service

---

## Decision

**Use GitHub Codespaces Secrets for all API keys and sensitive configuration.**

### Rationale

1. **Perfect Fit for Codespaces:** GitHub Codespaces Secrets are purpose-built for this exact use case
2. **Security by Default:** Secrets never touch git history or local filesystem
3. **Zero Friction:** Automatically available as environment variables in Python (`os.environ`)
4. **Team-Friendly:** Easy to share secrets across repository collaborators
5. **Maintainable:** Simple to rotate keys via GitHub UI

---

## Implementation

### Step 1: Configure Secrets in GitHub

**For Repository Secrets (Recommended):**
1. Navigate to: `https://github.com/[username]/Process_Software_Agents/settings/secrets/codespaces`
2. Or: Repository → Settings → Secrets and variables → Codespaces
3. Click "New repository secret"
4. Add each secret with name and value

**Required Secrets:**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `LANGFUSE_PUBLIC_KEY` | Langfuse public API key | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Langfuse secret API key | `sk-lf-...` |
| `LANGFUSE_HOST` | Langfuse instance URL | `https://cloud.langfuse.com` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | (Optional) OpenAI API key | `sk-...` |

**Optional Configuration Secrets:**

| Secret Name | Description | Default Value |
|-------------|-------------|---------------|
| `ENVIRONMENT` | Deployment environment | `development` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `TELEMETRY_ENABLED` | Enable/disable telemetry | `true` |

### Step 2: Access Secrets in Code

**Python example:**
```python
import os

# Access Langfuse credentials
langfuse_public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
langfuse_secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
langfuse_host = os.environ.get('LANGFUSE_HOST', 'https://cloud.langfuse.com')

# Access LLM provider keys
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
openai_key = os.environ.get('OPENAI_API_KEY')  # Optional

# Validate required secrets
if not langfuse_public_key:
    raise ValueError("LANGFUSE_PUBLIC_KEY not set. Add it to GitHub Codespaces Secrets.")
```

**With validation helper:**
```python
def validate_secrets():
    """Validate all required secrets are present."""
    required = [
        'LANGFUSE_PUBLIC_KEY',
        'LANGFUSE_SECRET_KEY',
        'ANTHROPIC_API_KEY',
    ]

    missing = [key for key in required if not os.environ.get(key)]

    if missing:
        raise ValueError(
            f"Missing required secrets: {', '.join(missing)}\n"
            f"Add them to: https://github.com/[repo]/settings/secrets/codespaces"
        )
```

### Step 3: Document for Team Members

**In README.md or SETUP.md:**
```markdown
## Setting Up Your Development Environment

### 1. Configure GitHub Codespaces Secrets

Before running the application, add the following secrets to the repository:

1. Go to: [Repository Secrets](https://github.com/[username]/Process_Software_Agents/settings/secrets/codespaces)
2. Add required secrets:
   - `LANGFUSE_PUBLIC_KEY` - Get from [Langfuse Dashboard](https://cloud.langfuse.com)
   - `LANGFUSE_SECRET_KEY` - Get from [Langfuse Dashboard](https://cloud.langfuse.com)
   - `LANGFUSE_HOST` - Set to `https://cloud.langfuse.com`
   - `ANTHROPIC_API_KEY` - Get from [Anthropic Console](https://console.anthropic.com)

3. Restart your Codespace for secrets to take effect

### 2. Verify Secrets Are Loaded

```bash
# Check secrets are available (values will be hidden)
echo $LANGFUSE_PUBLIC_KEY
echo $ANTHROPIC_API_KEY
```
```

### Step 4: Create Reference Documentation

Create `.env.example` as a **reference only** (not for actual secrets):
```bash
# .env.example - Reference for required environment variables
# DO NOT put real secrets here!
# Add actual values to GitHub Codespaces Secrets instead.

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-here
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM Provider Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here  # Optional
```

---

## Usage Guidelines

### For Individual Developers

1. **First-Time Setup:**
   - Add secrets to GitHub (one-time, requires repo admin)
   - Restart Codespace to load secrets
   - Run validation script to confirm

2. **Daily Development:**
   - Secrets automatically available in every Codespace
   - No manual configuration needed

3. **Key Rotation:**
   - Update secret value in GitHub UI
   - Restart Codespace
   - No code changes required

### For Team Leads / Admins

1. **Onboarding New Team Members:**
   - Add them as repository collaborators
   - They automatically inherit repository secrets
   - No need to share keys via Slack/email

2. **Key Rotation Schedule:**
   - Rotate Langfuse keys: Quarterly
   - Rotate LLM provider keys: When compromised or quarterly
   - Update in GitHub UI, notify team to restart Codespaces

3. **Audit Trail:**
   - GitHub logs all secret access and modifications
   - Review audit logs periodically

---

## Security Considerations

### What This Protects Against

 **Accidental git commits** - Secrets never in repository
 **Lost secrets on rebuild** - Persistent across Codespace lifecycles
 **Key sharing via insecure channels** - Team shares via GitHub, not Slack/email
 **Unauthorized access** - GitHub access controls determine who can view/edit

### What This Does NOT Protect Against

 **Malicious code in dependencies** - Can still access environment variables
 **Compromised GitHub account** - Attacker with repo access can view secrets
 **Print/logging of secrets** - Developers must avoid `print(os.environ)`

### Best Practices

1. **Never log secrets:** Avoid `print()` or `logger.debug()` of environment variables
2. **Minimal permissions:** Only add secrets with least privilege (e.g., read-only API keys where possible)
3. **Regular rotation:** Rotate keys quarterly or when team members leave
4. **Audit access:** Periodically review who has repository access
5. **Use .env.example:** Document required secrets without including values

---

## Migration Path

### From .env File to GitHub Secrets

If you currently have a `.env` file:

1. **Extract secrets:**
   ```bash
   cat .env  # Copy values to GitHub Secrets UI
   ```

2. **Add to GitHub:**
   - Manually add each secret to GitHub Codespaces Secrets

3. **Verify:**
   ```bash
   # Check environment variables are loaded
   env | grep LANGFUSE
   env | grep ANTHROPIC
   ```

4. **Clean up:**
   ```bash
   rm .env  # Delete local file
   git rm .env  # If accidentally committed
   ```

---

## Alternatives for Non-Codespaces Environments

If team members use **local development** (not Codespaces):

**Option A: Continue using GitHub Secrets (Recommended)**
- Use GitHub CLI to pull secrets locally:
  ```bash
  gh secret list
  gh secret set LANGFUSE_PUBLIC_KEY
  ```

**Option B: Hybrid Approach**
- GitHub Codespaces Secrets for Codespaces users
- `.env` file for local users (add `.env.example` as template)
- Code loads from `os.environ` regardless of source

---

## Validation

### Phase 1 Success Criteria (Week 1)
- [ ] All required secrets added to GitHub
- [ ] Team members can access secrets in Codespaces
- [ ] No secrets found in git history (`git log -S 'sk-lf-'`)
- [ ] Application successfully authenticates with Langfuse
- [ ] Application successfully calls Claude API

### Monitoring
- [ ] Set up alerts for API key usage anomalies (Langfuse dashboard)
- [ ] Review GitHub audit log monthly
- [ ] Verify secrets are not logged in application logs

---

## References

- **GitHub Codespaces Secrets Documentation:** https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces
- **Langfuse API Keys:** https://langfuse.com/docs/get-started
- **Anthropic API Keys:** https://docs.anthropic.com/claude/reference/getting-started-with-the-api
- **Security Best Practices:** OWASP Top 10 (A07:2021 - Identification and Authentication Failures)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-12 | Use GitHub Codespaces Secrets | Native integration, persistent, secure, team-friendly |

---

## Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| Technical Lead | Claude Code |  Approved | 2025-11-12 |
| Project Owner | TBD | Pending | |

---

**Status:**  **Accepted and Ready to Implement**

**Next Steps:**
1. Add secrets to GitHub Codespaces Secrets
2. Create `.env.example` reference file
3. Update README.md with setup instructions
4. Test secret access in Python code
5. Implement secret validation helper
