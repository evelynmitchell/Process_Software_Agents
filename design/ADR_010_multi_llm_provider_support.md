# ADR 010: Multi-LLM Provider Support

**Status:** In Progress (Phases 1-3, 5, 13 Complete)
**Date:** 2025-12-17
**Updated:** 2025-12-22
**Session:** 20251217.8
**Deciders:** User, Claude

## Context and Problem Statement

The current ASP implementation is **tightly coupled to Anthropic's API**, limiting flexibility and creating vendor lock-in. Users may want to:

1. **Use alternative providers** - OpenRouter for model variety, Gemini for Google's models
2. **Reduce costs** - Different providers have different pricing
3. **Local development** - Use Claude CLI without API keys
4. **Failover** - Switch providers if one is unavailable
5. **Experimentation** - Compare model quality across providers

### Current State

| Aspect | Current Implementation |
|--------|------------------------|
| SDK | `anthropic.Anthropic`, `anthropic.AsyncAnthropic` only |
| Error Handling | Anthropic-specific (`APIConnectionError`, `RateLimitError`, `APIStatusError`) |
| Cost Calculation | Hardcoded Anthropic pricing |
| Default Model | `claude-haiku-4-5` |
| Authentication | `ANTHROPIC_API_KEY` env var only |
| Configuration | No provider selection mechanism |

### Pain Points

```
Current: Single Provider
┌─────────────────────────────────────────────────────────────┐
│ BaseAgent → LLMClient → Anthropic SDK → Anthropic API      │
│                                                             │
│ No alternatives, no failover, vendor lock-in               │
└─────────────────────────────────────────────────────────────┘

Desired: Provider Abstraction
┌─────────────────────────────────────────────────────────────┐
│                    ┌─→ AnthropicProvider → Anthropic API   │
│ BaseAgent → LLM ──→├─→ OpenRouterProvider → OpenRouter API │
│             Client ├─→ GeminiProvider → Google AI API      │
│                    └─→ ClaudeCLIProvider → claude CLI      │
└─────────────────────────────────────────────────────────────┘
```

## Decision Drivers

1. **Flexibility** - Support multiple LLM providers with minimal code changes
2. **Consistency** - Unified interface regardless of provider
3. **Backward Compatibility** - Existing code using Anthropic should work unchanged
4. **Async Support** - All providers must support async (ADR 008)
5. **Cost Transparency** - Track costs per provider
6. **Configuration** - Easy provider selection via config/env vars
7. **Extensibility** - Easy to add new providers

## Proposed Providers

### Cloud Providers

| Provider | SDK/Method | Authentication | Use Case |
|----------|------------|----------------|----------|
| **Anthropic** | `anthropic` SDK | `ANTHROPIC_API_KEY` | Default, production |
| **OpenRouter** | OpenAI-compatible | `OPENROUTER_API_KEY` | Multi-model access (100+ models) |
| **Gemini** | `google-generativeai` | `GOOGLE_API_KEY` | Google models |
| **Groq** | OpenAI-compatible | `GROQ_API_KEY` | Ultra-fast inference (LPU) |
| **Together AI** | OpenAI-compatible | `TOGETHER_API_KEY` | 200+ models, <100ms latency |
| **Fireworks AI** | OpenAI-compatible | `FIREWORKS_API_KEY` | Fastest open-source serving |
| **DeepInfra** | OpenAI-compatible | `DEEPINFRA_API_KEY` | 100+ models, cost-effective |
| **Cloudflare Workers AI** | REST API / SDK | `CLOUDFLARE_API_TOKEN` | Serverless, edge inference |

### Local Providers

| Provider | SDK/Method | Authentication | Use Case |
|----------|------------|----------------|----------|
| **Ollama** | REST API / `ollama` | None (local) | Easy local models, CPU/GPU |
| **vLLM** | OpenAI-compatible | None (local) | High-performance local serving |
| **Claude CLI** | Subprocess | Local auth | Claude via CLI subscription |

### Provider Comparison

| Feature | Anthropic | OpenRouter | Gemini | Groq | Together | Fireworks | DeepInfra | Cloudflare | Ollama | vLLM |
|---------|-----------|------------|--------|------|----------|-----------|-----------|------------|--------|------|
| Models | Claude | 100+ | Gemini | Llama, Mixtral | 200+ | 50+ | 100+ | Various | Open | Any HF |
| API Style | Anthropic | OpenAI | Google | OpenAI | OpenAI | OpenAI | OpenAI | REST | OpenAI | OpenAI |
| Async | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Streaming | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Cost | $$$ | Varies | $$ | $ | $$ | $$ | $ | $ | Free | Free |
| Latency | ~1-3s | ~1-3s | ~1-2s | **~0.1s** | <100ms | **Fast** | ~1s | ~1s | Local | Local |
| Privacy | Cloud | Cloud | Cloud | Cloud | Cloud | Cloud | Cloud | Edge | **Local** | **Local** |
| GPU Req | No | No | No | No | No | No | No | No | Optional | Yes |

### Provider Details

#### Groq (Cloud - Ultra-Fast)
- **LPU Technology**: 18x faster than GPU-based inference
- **Speed**: 284 tokens/sec (Llama 3 70B), 876 tokens/sec (Llama 3 8B)
- **Models**: Llama 4, Qwen, Mixtral, Gemma, and more
- **API**: OpenAI-compatible, drop-in replacement
- **MCP Support**: Remote Model Context Protocol (Beta)

#### Together AI (Cloud - Scale)
- **Models**: 200+ open-source models
- **Latency**: Sub-100ms, automated optimization
- **Features**: Token caching, load balancing, model quantization
- **Enterprise**: Horizontal scaling, reliable infrastructure
- **API**: OpenAI-compatible at `https://api.together.xyz/v1`

#### Fireworks AI (Cloud - Speed)
- **FireAttention**: Proprietary optimized inference engine
- **Speed**: 4x lower latency than vLLM
- **Compliance**: HIPAA and SOC2 Type II certified
- **Multimodal**: Text, image, and audio inference
- **API**: OpenAI-compatible at `https://api.fireworks.ai/inference/v1`

#### DeepInfra (Cloud - Cost)
- **Models**: 100+ models including DeepSeek-V3
- **Pricing**: Cost-effective, usage-based billing
- **Features**: Dedicated instances, auto-scaling
- **Migration**: OpenAI-compatible for easy switching
- **API**: OpenAI-compatible at `https://api.deepinfra.com/v1/openai`

#### Cloudflare Workers AI (Cloud - Edge)
- **Serverless**: No infrastructure management
- **Edge**: Low latency, runs on Cloudflare's network
- **Models**: Llama, Mistral, and other open models
- **Python**: Native Workers support, LangChain integration

#### Ollama (Local - Easy Setup)
- **Zero Config**: `ollama run llama3` to get started
- **Models**: Llama 3, Mistral, CodeLlama, Qwen, Gemma, etc.
- **API**: OpenAI-compatible on port 11434
- **Hardware**: Works on CPU (slower) or GPU (fast)
- **Privacy**: Complete data privacy, no API keys

#### vLLM (Local - High Performance)
- **PagedAttention**: Efficient KV cache management
- **Performance**: Production-grade throughput
- **Models**: Any Hugging Face model
- **API**: OpenAI-compatible server
- **Requires**: GPU with sufficient VRAM

## Proposed Architecture

### 1. Provider Protocol (Interface)

**File:** `src/asp/providers/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator

@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""
    content: str | dict[str, Any]
    raw_content: str
    usage: dict[str, int]  # input_tokens, output_tokens
    cost: float | None
    model: str
    provider: str
    stop_reason: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout: float = 120.0
    max_retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str  # e.g., "anthropic", "openrouter", "gemini"

    @abstractmethod
    def call(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Synchronous LLM call."""
        ...

    @abstractmethod
    async def call_async(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Asynchronous LLM call."""
        ...

    @abstractmethod
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for token usage."""
        ...

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """List of available models for this provider."""
        ...
```

### 2. Provider Implementations

#### Anthropic Provider (Default)

**File:** `src/asp/providers/anthropic_provider.py`

```python
class AnthropicProvider(LLMProvider):
    name = "anthropic"

    MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-sonnet-4-20250514",
    ]

    PRICING = {  # Per million tokens
        "claude-opus-4-5": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
```

#### OpenRouter Provider

**File:** `src/asp/providers/openrouter_provider.py`

```python
class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    BASE_URL = "https://openrouter.ai/api/v1"

    # OpenRouter uses OpenAI-compatible API
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")

        # Use OpenAI client with custom base URL
        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/your-org/asp",
                "X-Title": "ASP Platform",
            }
        )
```

#### Gemini Provider

**File:** `src/asp/providers/gemini_provider.py`

```python
class GeminiProvider(LLMProvider):
    name = "gemini"

    MODELS = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        import google.generativeai as genai
        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.genai = genai
```

#### Claude CLI Provider

**File:** `src/asp/providers/claude_cli_provider.py`

```python
class ClaudeCLIProvider(LLMProvider):
    name = "claude_cli"

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        # Verify claude CLI is available
        self._check_cli_available()

    async def call_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Run claude CLI as subprocess."""
        process = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        # Parse and return response
        ...
```

#### Groq Provider (Ultra-Fast LPU)

**File:** `src/asp/providers/groq_provider.py`

```python
class GroqProvider(LLMProvider):
    """
    Groq provider using LPU (Language Processing Unit) for ultra-fast inference.
    18x faster than GPU-based inference.
    """
    name = "groq"

    BASE_URL = "https://api.groq.com/openai/v1"

    # Current models as of Dec 2025
    MODELS = [
        "llama-3.3-70b-versatile",      # Meta - latest Llama
        "llama-3.1-8b-instant",          # Meta - fast inference
        "llama3-70b-8192",               # Meta - 8K context
        "llama3-8b-8192",                # Meta - 8K context
        "gemma2-9b-it",                  # Google
        "mixtral-8x7b-32768",            # Mistral - 32K context
        "llama-guard-3-8b",              # Meta - safety/moderation
    ]

    # Groq uses OpenAI-compatible API
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("GROQ_API_KEY")

        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)
```

#### Together AI Provider (Scale)

**File:** `src/asp/providers/together_provider.py`

```python
class TogetherProvider(LLMProvider):
    """
    Together AI provider for 200+ open-source models.
    Sub-100ms latency with automated optimization.
    """
    name = "together"

    BASE_URL = "https://api.together.xyz/v1"

    # Popular models as of Dec 2025
    MODELS = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "meta-llama/Llama-3.1-8B-Instruct-Turbo",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "google/gemma-2-27b-it",
    ]

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("TOGETHER_API_KEY")

        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)
```

#### Fireworks AI Provider (Speed)

**File:** `src/asp/providers/fireworks_provider.py`

```python
class FireworksProvider(LLMProvider):
    """
    Fireworks AI provider with FireAttention for fastest inference.
    4x lower latency than vLLM. HIPAA/SOC2 compliant.
    """
    name = "fireworks"

    BASE_URL = "https://api.fireworks.ai/inference/v1"

    # Popular models as of Dec 2025
    MODELS = [
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "accounts/fireworks/models/mixtral-8x22b-instruct",
        "accounts/fireworks/models/qwen2p5-72b-instruct",
        "accounts/fireworks/models/deepseek-r1",
    ]

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("FIREWORKS_API_KEY")

        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)
```

#### DeepInfra Provider (Cost)

**File:** `src/asp/providers/deepinfra_provider.py`

```python
class DeepInfraProvider(LLMProvider):
    """
    DeepInfra provider for cost-effective inference.
    100+ models with OpenAI-compatible API.
    """
    name = "deepinfra"

    BASE_URL = "https://api.deepinfra.com/v1/openai"

    # Popular models as of Dec 2025
    MODELS = [
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "Qwen/Qwen2.5-72B-Instruct",
        "deepseek-ai/DeepSeek-V3",
        "google/gemma-2-27b-it",
    ]

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        api_key = self.config.api_key or os.getenv("DEEPINFRA_API_KEY")

        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)
```

#### Ollama Provider (Local)

**File:** `src/asp/providers/ollama_provider.py`

```python
class OllamaProvider(LLMProvider):
    """
    Ollama provider for local model serving.
    Zero API keys, complete privacy, runs on CPU or GPU.
    """
    name = "ollama"

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    # Popular models as of Dec 2025 (by pull count)
    MODELS = [
        "llama3.1",           # 107M pulls - Meta's flagship
        "deepseek-r1",        # 74M pulls - reasoning model
        "gemma3",             # 28M pulls - Google's latest
        "mistral",            # 23M pulls - Mistral 7B v0.3
        "qwen2.5",            # 18M pulls - Alibaba 128K context
        "gemma2",             # 11M pulls - Google 2B/9B/27B
        "llava",              # 12M pulls - multimodal
        "codellama",          # Code-optimized
        "qwen3-coder",        # 1.3M pulls - coding
        "gpt-oss",            # 5.3M pulls - OpenAI open weights
    ]

    # Ollama provides OpenAI-compatible API
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        base_url = self.config.base_url or os.getenv("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)

        from openai import OpenAI, AsyncOpenAI
        # Ollama doesn't require API key
        self.client = OpenAI(api_key="ollama", base_url=base_url)
        self.async_client = AsyncOpenAI(api_key="ollama", base_url=base_url)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Local models are free."""
        return 0.0
```

#### vLLM Provider (Local High-Performance)

**File:** `src/asp/providers/vllm_provider.py`

```python
class VLLMProvider(LLMProvider):
    """
    vLLM provider for high-performance local inference.
    Uses PagedAttention for efficient KV cache management.
    Supports any Hugging Face transformers model.
    """
    name = "vllm"

    DEFAULT_BASE_URL = "http://localhost:8000/v1"

    # vLLM can serve any HF model, common examples:
    EXAMPLE_MODELS = [
        "meta-llama/Llama-3.1-8B-Instruct",
        "meta-llama/Llama-3.1-70B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "Qwen/Qwen2.5-72B-Instruct",
        "deepseek-ai/DeepSeek-V3",
        "google/gemma-2-9b-it",
    ]

    # vLLM serves OpenAI-compatible API
    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        base_url = self.config.base_url or os.getenv("VLLM_BASE_URL", self.DEFAULT_BASE_URL)

        from openai import OpenAI, AsyncOpenAI
        self.client = OpenAI(api_key="vllm", base_url=base_url)
        self.async_client = AsyncOpenAI(api_key="vllm", base_url=base_url)

    @property
    def available_models(self) -> list[str]:
        """Query vLLM server for available models."""
        response = self.client.models.list()
        return [m.id for m in response.data]

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Local models are free (compute cost not tracked)."""
        return 0.0
```

#### Cloudflare Workers AI Provider (Edge)

**File:** `src/asp/providers/cloudflare_provider.py`

```python
class CloudflareProvider(LLMProvider):
    """
    Cloudflare Workers AI provider for serverless edge inference.
    Low latency, runs on Cloudflare's global network.
    """
    name = "cloudflare"

    BASE_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"

    # Current models as of Dec 2025
    MODELS = [
        "@cf/openai/gpt-oss-120b",                    # OpenAI - production/reasoning
        "@cf/openai/gpt-oss-20b",                     # OpenAI - lower latency
        "@cf/meta/llama-4-scout-17b-16e-instruct",   # Meta - multimodal MoE
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",  # Meta - quantized fast
        "@cf/meta/llama-3.1-8b-instruct-fast",       # Meta - optimized
        "@cf/google/gemma-3-12b-it",                 # Google - 128K context
        "@cf/qwen/qwen3-30b-a3b-fp8",                # Qwen - reasoning/agent
        "@cf/qwen/qwq-32b",                          # Qwen - reasoning
        "@cf/deepseek/deepseek-r1-distill-qwen-32b", # DeepSeek - reasoning
        "@cf/mistral/mistral-small-3.1-24b-instruct", # Mistral - vision
    ]

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig()
        self.api_token = self.config.api_key or os.getenv("CLOUDFLARE_API_TOKEN")
        self.account_id = self.config.extra.get("account_id") or os.getenv("CLOUDFLARE_ACCOUNT_ID")

    async def call_async(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        """Call Cloudflare Workers AI REST API."""
        import httpx
        model = model or self.MODELS[0]
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"prompt": prompt, **kwargs},
            )
            data = response.json()
            return LLMResponse(
                content=data["result"]["response"],
                raw_content=data["result"]["response"],
                usage={},  # Cloudflare doesn't always return token counts
                cost=None,
                model=model,
                provider="cloudflare",
                stop_reason=None,
            )
```

### 3. Provider Registry

**File:** `src/asp/providers/registry.py`

```python
class ProviderRegistry:
    """Registry for LLM providers."""

    _providers: dict[str, type[LLMProvider]] = {}
    _instances: dict[str, LLMProvider] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[LLMProvider]):
        """Register a provider class."""
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name: str, config: ProviderConfig | None = None) -> LLMProvider:
        """Get or create a provider instance."""
        if name not in cls._instances:
            if name not in cls._providers:
                raise ValueError(f"Unknown provider: {name}")
            cls._instances[name] = cls._providers[name](config)
        return cls._instances[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List registered providers."""
        return list(cls._providers.keys())

# Auto-register built-in providers
# Cloud providers
ProviderRegistry.register("anthropic", AnthropicProvider)
ProviderRegistry.register("openrouter", OpenRouterProvider)
ProviderRegistry.register("gemini", GeminiProvider)
ProviderRegistry.register("groq", GroqProvider)
ProviderRegistry.register("together", TogetherProvider)
ProviderRegistry.register("fireworks", FireworksProvider)
ProviderRegistry.register("deepinfra", DeepInfraProvider)
ProviderRegistry.register("cloudflare", CloudflareProvider)

# Local providers
ProviderRegistry.register("ollama", OllamaProvider)
ProviderRegistry.register("vllm", VLLMProvider)
ProviderRegistry.register("claude_cli", ClaudeCLIProvider)
```

### 4. Updated LLMClient

**File:** `src/asp/utils/llm_client.py`

```python
class LLMClient:
    """
    Multi-provider LLM client.

    Supports Anthropic (default), OpenRouter, Gemini, and Claude CLI.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        config: ProviderConfig | None = None,
    ):
        self.provider_name = provider
        self.provider = ProviderRegistry.get(provider, config)

    def call_with_retry(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Call LLM with retry logic (delegates to provider)."""
        response = self.provider.call(prompt, **kwargs)
        return response.to_dict()

    async def call_with_retry_async(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Async call with retry logic."""
        response = await self.provider.call_async(prompt, **kwargs)
        return response.to_dict()
```

### 5. Configuration

#### Environment Variables

```bash
# Provider selection
ASP_LLM_PROVIDER=anthropic  # or openrouter, gemini, groq, together, fireworks, deepinfra, cloudflare, ollama, vllm, claude_cli

# Cloud provider API keys
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...
TOGETHER_API_KEY=...
FIREWORKS_API_KEY=...
DEEPINFRA_API_KEY=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...

# Local provider URLs (optional, defaults shown)
OLLAMA_BASE_URL=http://localhost:11434/v1
VLLM_BASE_URL=http://localhost:8000/v1

# Optional: Override default model
ASP_DEFAULT_MODEL=claude-sonnet-4-5
```

#### CLI Integration

```bash
# Use default provider (Anthropic)
python -m asp.cli run --task-id TASK-001 --description "..."

# Use specific cloud provider
python -m asp.cli run --task-id TASK-001 --description "..." --provider openrouter
python -m asp.cli run --task-id TASK-001 --description "..." --provider groq
python -m asp.cli run --task-id TASK-001 --description "..." --provider gemini

# Use local provider (no API key needed)
python -m asp.cli run --task-id TASK-001 --description "..." --provider ollama
python -m asp.cli run --task-id TASK-001 --description "..." --provider vllm

# Use specific model
python -m asp.cli run --task-id TASK-001 --description "..." --provider openrouter --model anthropic/claude-3-opus
python -m asp.cli run --task-id TASK-001 --description "..." --provider groq --model llama-3.3-70b-versatile
python -m asp.cli run --task-id TASK-001 --description "..." --provider ollama --model deepseek-r1
```

## Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Provider abstraction layer (`LLMProvider`, `LLMResponse`) | **Complete** |
| Phase 2 | Refactor `AnthropicProvider` from existing `LLMClient` | **Complete** |
| Phase 3 | Add `OpenRouterProvider` (OpenAI-compatible) | **Complete** |
| Phase 4 | Add `GeminiProvider` | Pending |
| Phase 5 | Add `GroqProvider` (OpenAI-compatible, ultra-fast) | **Complete** |
| Phase 6 | Add `TogetherProvider` (OpenAI-compatible, scale) | Pending |
| Phase 7 | Add `FireworksProvider` (OpenAI-compatible, speed) | Pending |
| Phase 8 | Add `DeepInfraProvider` (OpenAI-compatible, cost) | Pending |
| Phase 9 | Add `OllamaProvider` (local, OpenAI-compatible) | Pending |
| Phase 10 | Add `VLLMProvider` (local, OpenAI-compatible) | Pending |
| Phase 11 | Add `CloudflareProvider` (REST API) | Pending |
| Phase 12 | Add `ClaudeCLIProvider` (subprocess) | Pending |
| Phase 13 | CLI integration (`--provider`, `--model` flags) | **Complete** |
| Phase 14 | Documentation updates | Pending |

**Note:** Phases 3, 5-10 share OpenAI-compatible implementation - can be done quickly with a base class.

### Phase 1: Provider Abstraction (This Session)

Create the foundation:
- `LLMResponse` dataclass
- `ProviderConfig` dataclass
- `LLMProvider` abstract base class
- `ProviderRegistry` for provider management
- Error types (`ProviderError`, `RateLimitError`, `AuthenticationError`)

### Phase 2: Anthropic Provider

Refactor existing `LLMClient` code into `AnthropicProvider`:
- Move Anthropic-specific code to new provider
- Keep `LLMClient` as thin wrapper
- Maintain backward compatibility

### Phase 3-5: Additional Providers

Add providers one at a time, each with:
- Full sync/async support
- Retry logic
- Cost estimation
- Model listing
- Unit tests

### Phase 6: CLI Integration

- Add `--provider` flag to CLI
- Add `--model` flag for explicit model selection
- Update help text and examples

## Alternatives Considered

### Option A: Use aisuite (Andrew Ng's Library)

Use [aisuite](https://github.com/andrewyng/aisuite) as the abstraction layer.

**Pros:**
- Lightweight, minimal dependencies
- Simple `provider:model` syntax (e.g., `anthropic:claude-3-5-sonnet`)
- MCP (Model Context Protocol) support built-in
- Backed by Andrew Ng's team
- OpenAI-style API, familiar to most developers

**Cons:**
- No streaming support yet (as of late 2024)
- No rate limit handling
- No token usage monitoring
- Still early/maturing
- Fewer providers than LiteLLM

**Example:**
```python
import aisuite as ai
client = ai.Client()
response = client.chat.completions.create(
    model="anthropic:claude-3-5-sonnet",  # or "openai:gpt-4o", "groq:llama-3.1-70b"
    messages=[{"role": "user", "content": "Hello!"}],
)
```

**Decision:** Strong candidate for lightweight use cases. Consider adopting.

---

### Option B: Use LiteLLM

Use [LiteLLM](https://github.com/BerriAI/litellm) as abstraction layer.

**Pros:**
- Most comprehensive: 100+ providers supported
- Battle-tested, widely used
- Handles provider differences automatically
- Streaming, async, function calling support
- Cost tracking built-in
- Fallback/retry logic included

**Cons:**
- Heavier dependency
- Known performance issues at scale (memory leaks, latency)
- Less control over behavior
- May be overkill for our needs

**Example:**
```python
from litellm import completion

response = completion(
    model="claude-3-5-sonnet-20241022",  # or "gpt-4", "gemini/gemini-pro"
    messages=[{"role": "user", "content": "Hello!"}],
)
```

**Decision:** Good for feature completeness. Consider for production if scaling issues are addressed.

---

### Option C: Build Custom Abstraction (Current Proposal)

Build our own provider abstraction layer as proposed in this ADR.

**Pros:**
- Full control over behavior
- Tailored to ASP needs
- No external dependencies for core functionality
- Can optimize for our specific use cases
- Educational value

**Cons:**
- More work to build and maintain
- Need to handle edge cases ourselves
- May reinvent the wheel

**Decision:** Current proposal. Gives most control but highest effort.

---

### Option D: Hybrid Approach

Use aisuite or LiteLLM internally, wrapped in our own interface.

**Pros:**
- Leverage existing library for heavy lifting
- Our interface for consistency
- Can swap underlying library later
- Best of both worlds

**Cons:**
- Extra abstraction layer
- Dependency on external library

**Example:**
```python
# Our interface wraps aisuite/LiteLLM
class LLMClient:
    def __init__(self, provider: str = "anthropic"):
        import aisuite as ai  # or litellm
        self._client = ai.Client()
        self._provider = provider

    def call(self, prompt: str, model: str = None) -> LLMResponse:
        model = model or f"{self._provider}:claude-3-5-sonnet"
        response = self._client.chat.completions.create(...)
        return LLMResponse.from_aisuite(response)
```

**Decision:** Recommended approach - use aisuite for simplicity, wrap in our interface.

---

### Option E: OpenAI-Compatible Only

Only support providers with OpenAI-compatible APIs.

**Pros:**
- Single client implementation (OpenAI SDK)
- Works with: OpenRouter, Groq, Ollama, vLLM, Together AI, etc.
- Simpler code

**Cons:**
- Excludes native Anthropic SDK (though OpenRouter provides Claude)
- Excludes native Gemini SDK
- Loses provider-specific features

**Decision:** Viable but limiting. Many providers now offer OpenAI-compatible endpoints.

---

### Option F: Keep Anthropic Only

Don't add provider abstraction.

**Pros:**
- No additional complexity
- Current code works
- Anthropic models are excellent

**Cons:**
- Vendor lock-in
- No flexibility for cost optimization
- No local development option
- Users explicitly requested alternatives

**Decision:** Rejected - user explicitly requested multi-provider support.

---

### Recommendation Matrix

| Option | Effort | Flexibility | Control | Maintenance |
|--------|--------|-------------|---------|-------------|
| A: aisuite | Low | Medium | Low | External |
| B: LiteLLM | Low | High | Low | External |
| C: Custom | High | High | High | Internal |
| D: Hybrid | Medium | High | Medium | Mixed |
| E: OpenAI-only | Medium | Medium | Medium | Internal |
| F: Anthropic-only | None | None | N/A | Current |

**Recommended: Option D (Hybrid)** - Use aisuite as the underlying library, wrapped in our own `LLMClient` interface for consistency and future flexibility.

## Consequences

### Positive

- **Flexibility** - Users can choose their preferred provider
- **Cost Optimization** - Switch to cheaper providers for dev/testing
- **Resilience** - Failover to alternative providers
- **Experimentation** - Compare model quality easily

### Negative

- **Complexity** - More code to maintain
- **Testing** - Need to test each provider
- **Dependencies** - Additional SDKs to manage

### Neutral

- **Breaking Changes** - None if we maintain backward compatibility
- **Performance** - Similar across providers (network-bound)

## Technical Notes

### Error Handling Strategy

Map provider-specific errors to common types:

```python
class ProviderError(Exception):
    """Base error for provider issues."""
    pass

class RateLimitError(ProviderError):
    """Rate limit exceeded."""
    retry_after: float | None = None

class AuthenticationError(ProviderError):
    """Invalid or missing credentials."""
    pass

class ModelNotFoundError(ProviderError):
    """Requested model not available."""
    pass
```

### Model Name Normalization

OpenRouter uses prefixed model names:

| OpenRouter | Native |
|------------|--------|
| `anthropic/claude-3-opus` | `claude-3-opus-20240229` |
| `openai/gpt-4` | `gpt-4` |
| `google/gemini-pro` | `gemini-pro` |

Consider a model name mapping utility.

### Cost Tracking

Each provider has different pricing. Track costs per-call and aggregate:

```python
@dataclass
class CostSummary:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime
```

## References

### Provider SDKs & Documentation
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)
- [OpenRouter API](https://openrouter.ai/docs)
- [Google Generative AI](https://ai.google.dev/gemini-api/docs)
- [Groq API](https://console.groq.com/docs/overview)
- [Together AI API](https://docs.together.ai/)
- [Fireworks AI API](https://docs.fireworks.ai/)
- [DeepInfra API](https://deepinfra.com/docs)
- [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/)
- [Ollama](https://github.com/ollama/ollama)
- [vLLM](https://docs.vllm.ai/)
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli)

### Abstraction Libraries
- [aisuite](https://github.com/andrewyng/aisuite) - Andrew Ng's lightweight multi-provider library
- [LiteLLM](https://github.com/BerriAI/litellm) - Comprehensive 100+ provider support
- [Instructor](https://python.useinstructor.com/) - Structured outputs across providers
- [llm](https://pypi.org/project/llm/) - Simon Willison's CLI + Python library

### Related Resources
- [LiteLLM Alternatives 2025](https://dev.to/debmckinney/top-5-litellm-alternatives-in-2025-1pki)
- [Top 11 LLM API Providers 2025](https://www.helicone.ai/blog/llm-api-providers)
- [LLM API Providers Leaderboard](https://artificialanalysis.ai/leaderboards/providers)
- [vLLM Quickstart](https://docs.vllm.ai/en/v0.9.2/getting_started/quickstart.html)
- [Groq LPU Technology](https://groq.com/)
