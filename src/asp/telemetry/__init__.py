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

import asp.telemetry.config as config
import asp.telemetry.telemetry as telemetry_module

configure_anthropic_instrumentation = config.configure_anthropic_instrumentation
configure_httpx_instrumentation = config.configure_httpx_instrumentation
configure_logfire = config.configure_logfire
configure_openai_instrumentation = config.configure_openai_instrumentation
configure_pydantic_plugin = config.configure_pydantic_plugin
ensure_llm_instrumentation = config.ensure_llm_instrumentation
get_telemetry_provider = config.get_telemetry_provider
initialize_telemetry = config.initialize_telemetry
instrument_all_llm_providers = config.instrument_all_llm_providers
is_langfuse_available = config.is_langfuse_available
is_logfire_available = config.is_logfire_available

get_db_connection = telemetry_module.get_db_connection
get_langfuse_client = telemetry_module.get_langfuse_client
insert_agent_cost = telemetry_module.insert_agent_cost
insert_defect = telemetry_module.insert_defect
log_agent_metric = telemetry_module.log_agent_metric
log_defect = telemetry_module.log_defect
log_defect_manual = telemetry_module.log_defect_manual
track_agent_cost = telemetry_module.track_agent_cost

__all__ = [
    # Core decorators
    "track_agent_cost",
    "log_defect",
    # Main initialization
    "initialize_telemetry",
    "ensure_llm_instrumentation",
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
