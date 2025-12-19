"""
Provider error types.

This module defines a hierarchy of exceptions for LLM provider errors,
enabling consistent error handling across different providers.

Author: ASP Development Team
Date: December 2025
"""

from typing import Any


class ProviderError(Exception):
    """
    Base exception for all provider errors.

    Attributes:
        message: Human-readable error message
        provider: Name of the provider that raised the error
        details: Additional error details (provider-specific)
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.provider:
            return f"[{self.provider}] {self.message}"
        return self.message


class RateLimitError(ProviderError):
    """
    Rate limit exceeded.

    The provider's rate limit has been reached. Callers should
    wait before retrying.

    Attributes:
        retry_after: Suggested wait time in seconds (if provided by API)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        provider: str | None = None,
        retry_after: float | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """
    Authentication failed.

    The API key is invalid, expired, or missing.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)


class ModelNotFoundError(ProviderError):
    """
    Requested model not available.

    The specified model is not available from this provider.

    Attributes:
        model: The model that was requested
        available_models: List of available models (if known)
    """

    def __init__(
        self,
        message: str = "Model not found",
        provider: str | None = None,
        model: str | None = None,
        available_models: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)
        self.model = model
        self.available_models = available_models


class ConnectionError(ProviderError):
    """
    Network connection failed.

    Unable to connect to the provider's API endpoint.
    """

    def __init__(
        self,
        message: str = "Connection failed",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)


class TimeoutError(ProviderError):
    """
    Request timed out.

    The request took too long to complete.

    Attributes:
        timeout: The timeout value in seconds
    """

    def __init__(
        self,
        message: str = "Request timed out",
        provider: str | None = None,
        timeout: float | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)
        self.timeout = timeout


class InvalidRequestError(ProviderError):
    """
    Invalid request parameters.

    The request contained invalid parameters that the provider rejected.
    This is typically a client-side error that should not be retried.
    """

    def __init__(
        self,
        message: str = "Invalid request",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)


class ContentFilterError(ProviderError):
    """
    Content was filtered by the provider.

    The request or response triggered the provider's content filters.
    """

    def __init__(
        self,
        message: str = "Content filtered",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, provider, details)
