"""Telemetry module for ASP Platform.

Supports multiple backends:
- Logfire (Pydantic's observability platform) - recommended
- Langfuse (LLM observability) - legacy support
- SQLite (persistent local storage) - always enabled

Configure via ASP_TELEMETRY_PROVIDER environment variable:
- "logfire" (recommended)
- "langfuse" (default for backward compatibility)
- "none" (disable cloud telemetry, SQLite still works)
"""

from .config import (
    configure_anthropic_instrumentation,
    configure_httpx_instrumentation,
    configure_logfire,
    configure_openai_instrumentation,
    configure_pydantic_plugin,
    get_telemetry_provider,
    instrument_all_llm_providers,
    is_langfuse_available,
    is_logfire_available,
)
from .telemetry import (
    get_db_connection,
    get_langfuse_client,
    insert_agent_cost,
    insert_defect,
    log_agent_metric,
    log_defect,
    log_defect_manual,
    track_agent_cost,
)

__all__ = [
    # Core decorators
    "track_agent_cost",
    "log_defect",
    # Configuration
    "get_telemetry_provider",
    "configure_logfire",
    "configure_pydantic_plugin",
    "configure_anthropic_instrumentation",
    "configure_openai_instrumentation",
    "configure_httpx_instrumentation",
    "instrument_all_llm_providers",
    # Availability checks
    "is_logfire_available",
    "is_langfuse_available",
    # Legacy Langfuse
    "get_langfuse_client",
    # Database helpers
    "get_db_connection",
    "insert_agent_cost",
    "insert_defect",
    "log_agent_metric",
    "log_defect_manual",
]
