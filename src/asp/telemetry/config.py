"""
Telemetry Configuration for ASP Platform.

Provides centralized telemetry configuration with environment-based provider selection.
Supports both Langfuse (current) and Logfire (new) backends.

Environment Variables:
    ASP_TELEMETRY_PROVIDER: Select backend ("logfire", "langfuse", "none")
    ASP_ENVIRONMENT: Environment name (development, staging, production)
    ASP_VERSION: Service version string
    ASP_TELEMETRY_CONSOLE: Enable console output for debugging ("true"/"false")

    # Logfire-specific
    LOGFIRE_TOKEN: Logfire project write token
    LOGFIRE_PROJECT_NAME: Logfire project name
    LOGFIRE_SEND: Whether to send to Logfire cloud ("true"/"false")

    # Langfuse-specific
    LANGFUSE_PUBLIC_KEY: Langfuse public key
    LANGFUSE_SECRET_KEY: Langfuse secret key
    LANGFUSE_HOST: Langfuse host URL (for self-hosted)

Author: ASP Development Team
Date: December 2025
"""

import os
from typing import Literal

# Provider type alias
TelemetryProvider = Literal["logfire", "langfuse", "none"]

# Lazy initialization flags
_logfire_initialized = False
_langfuse_initialized = False
_llm_instrumentation_done = False


def get_telemetry_provider() -> TelemetryProvider:
    """
    Get the configured telemetry provider.

    Resolution order:
    1. ASP_TELEMETRY_PROVIDER environment variable
    2. Default to "langfuse" for backward compatibility

    Returns:
        TelemetryProvider: One of "logfire", "langfuse", or "none"
    """
    provider = os.getenv("ASP_TELEMETRY_PROVIDER", "langfuse").lower()
    if provider in ("logfire", "langfuse", "none"):
        return provider
    # Invalid value, fall back to langfuse for backward compatibility
    return "langfuse"


def configure_logfire(
    service_name: str = "asp-platform",
    environment: str | None = None,
    send_to_logfire: bool | None = None,
) -> bool:
    """
    Configure Logfire for the ASP platform.

    Args:
        service_name: Name of the service for tracing
        environment: Environment name (dev, staging, prod). Auto-detected if None.
        send_to_logfire: Whether to send data to Logfire cloud. Auto-detected if None.

    Returns:
        bool: True if configuration succeeded, False otherwise
    """
    global _logfire_initialized

    if _logfire_initialized:
        return True

    try:
        import logfire
    except ImportError:
        print("Warning: logfire not installed. Run: pip install logfire")
        return False

    # Resolve environment
    environment = environment or os.getenv("ASP_ENVIRONMENT", "development")

    # Resolve send_to_logfire
    if send_to_logfire is None:
        send_to_logfire = os.getenv("LOGFIRE_SEND", "true").lower() == "true"

    # Configure Logfire
    logfire.configure(
        service_name=service_name,
        service_version=os.getenv("ASP_VERSION", "0.1.0"),
        environment=environment,
        send_to_logfire=send_to_logfire,
        console=os.getenv("ASP_TELEMETRY_CONSOLE", "false").lower() == "true",
    )

    _logfire_initialized = True
    return True


def configure_pydantic_plugin(record: str = "failure") -> bool:
    """
    Configure Pydantic plugin for Logfire.

    This captures validation events for ASP models:
    - Validation success/failure rates
    - Field-level validation errors
    - Validation timing
    - Schema usage analytics

    Args:
        record: What to record ("all", "failure", "metrics")

    Returns:
        bool: True if configuration succeeded, False otherwise
    """
    try:
        import logfire
    except ImportError:
        return False

    # Pydantic plugin is configured during logfire.configure()
    # This function is for re-configuration if needed
    logfire.configure(
        pydantic_plugin=logfire.PydanticPlugin(record=record),
    )
    return True


def configure_anthropic_instrumentation() -> bool:
    """
    Enable automatic instrumentation for Anthropic API calls.

    This captures:
    - Request/response content
    - Token usage (input, output, total)
    - Latency
    - Model selection
    - Stop reason

    Returns:
        bool: True if instrumentation succeeded, False otherwise
    """
    try:
        import logfire

        # Try to instrument Anthropic if the method exists
        if hasattr(logfire, "instrument_anthropic"):
            logfire.instrument_anthropic()
            return True
        else:
            # Logfire version might not have this method
            print("Warning: logfire.instrument_anthropic not available in this version")
            return False
    except ImportError:
        print("Warning: logfire not installed")
        return False
    except Exception as e:
        print(f"Warning: Failed to instrument Anthropic: {e}")
        return False


def configure_openai_instrumentation() -> bool:
    """
    Enable automatic instrumentation for OpenAI API calls.

    Returns:
        bool: True if instrumentation succeeded, False otherwise
    """
    try:
        import logfire

        if hasattr(logfire, "instrument_openai"):
            logfire.instrument_openai()
            return True
        else:
            print("Warning: logfire.instrument_openai not available in this version")
            return False
    except ImportError:
        print("Warning: logfire not installed")
        return False
    except Exception as e:
        print(f"Warning: Failed to instrument OpenAI: {e}")
        return False


def configure_httpx_instrumentation() -> bool:
    """
    Enable automatic instrumentation for HTTPX client calls.

    Returns:
        bool: True if instrumentation succeeded, False otherwise
    """
    try:
        import logfire

        if hasattr(logfire, "instrument_httpx"):
            logfire.instrument_httpx()
            return True
        else:
            return False
    except ImportError:
        return False
    except Exception as e:
        print(f"Warning: Failed to instrument HTTPX: {e}")
        return False


def instrument_all_llm_providers() -> dict[str, bool]:
    """
    Instrument all supported LLM providers.

    Returns:
        dict: Mapping of provider name to success status
    """
    return {
        "anthropic": configure_anthropic_instrumentation(),
        "openai": configure_openai_instrumentation(),
        "httpx": configure_httpx_instrumentation(),
    }


def initialize_telemetry(
    service_name: str = "asp-platform",
    instrument_llm: bool = True,
) -> dict[str, any]:
    """
    Initialize telemetry for the ASP platform.

    This is the main entry point for telemetry setup. Call this early in your
    application startup, BEFORE creating any LLM clients (Anthropic, OpenAI).

    Args:
        service_name: Name of the service for tracing
        instrument_llm: Whether to instrument LLM providers (default True)

    Returns:
        dict: Status of initialization
            {
                "provider": "logfire" | "langfuse" | "none",
                "logfire_configured": bool,
                "llm_instrumentation": {"anthropic": bool, "openai": bool, ...}
            }

    Example:
        # At application startup (before creating LLM clients)
        from asp.telemetry import initialize_telemetry
        status = initialize_telemetry()
        print(f"Telemetry provider: {status['provider']}")

        # Now safe to create LLM clients
        from asp.utils.llm_client import LLMClient
        client = LLMClient()  # Will be automatically instrumented
    """
    global _llm_instrumentation_done

    provider = get_telemetry_provider()
    result = {
        "provider": provider,
        "logfire_configured": False,
        "llm_instrumentation": {},
    }

    if provider == "logfire":
        # Configure Logfire first
        result["logfire_configured"] = configure_logfire(service_name=service_name)

        # Then instrument LLM providers (must be done BEFORE creating clients)
        if instrument_llm and not _llm_instrumentation_done:
            result["llm_instrumentation"] = instrument_all_llm_providers()
            _llm_instrumentation_done = True

    elif provider == "langfuse":
        # Langfuse doesn't require pre-initialization
        result["logfire_configured"] = False
        result["llm_instrumentation"] = {}

    return result


def ensure_llm_instrumentation() -> bool:
    """
    Ensure LLM instrumentation is set up.

    Call this before creating LLM clients if you're not using initialize_telemetry().
    Safe to call multiple times - only instruments once.

    Returns:
        bool: True if instrumentation was set up (or already done), False otherwise
    """
    global _llm_instrumentation_done

    if _llm_instrumentation_done:
        return True

    provider = get_telemetry_provider()
    if provider != "logfire":
        return False

    # Configure logfire if not done
    configure_logfire()

    # Instrument LLM providers
    results = instrument_all_llm_providers()
    _llm_instrumentation_done = True

    return any(results.values())


def is_logfire_available() -> bool:
    """Check if Logfire is available for use."""
    try:
        import logfire  # noqa: F401

        return True
    except ImportError:
        return False


def is_langfuse_available() -> bool:
    """Check if Langfuse is available for use."""
    try:
        from langfuse import Langfuse  # noqa: F401

        return True
    except ImportError:
        return False
