"""
Tests for asp.telemetry.config module.

Tests the telemetry configuration for the ASP platform.
"""

import os
import sys
from unittest import mock


class TestGetTelemetryProvider:
    """Tests for get_telemetry_provider function."""

    def test_default_provider_is_langfuse(self):
        """Test default provider is langfuse."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ASP_TELEMETRY_PROVIDER", None)
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "langfuse"

    def test_logfire_provider(self):
        """Test logfire provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "logfire"}):
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "logfire"

    def test_langfuse_provider(self):
        """Test langfuse provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "langfuse"}):
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "langfuse"

    def test_none_provider(self):
        """Test none provider selection."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "none"}):
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "none"

    def test_invalid_provider_defaults_to_langfuse(self):
        """Test invalid provider defaults to langfuse."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "invalid"}):
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "langfuse"

    def test_case_insensitive(self):
        """Test provider selection is case insensitive."""
        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "LOGFIRE"}):
            from asp.telemetry.config import get_telemetry_provider

            assert get_telemetry_provider() == "logfire"


class TestConfigureLogfire:
    """Tests for configure_logfire function."""

    def test_configure_logfire_success(self):
        """Test successful Logfire configuration."""
        import asp.telemetry.config as config_module

        # Reset initialization flag
        config_module._logfire_initialized = False

        mock_logfire = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_logfire

            result = configure_logfire(service_name="test-service")

            assert result is True
            mock_logfire.configure.assert_called_once()

        # Reset for next test
        config_module._logfire_initialized = False

    def test_configure_logfire_already_initialized(self):
        """Test Logfire returns True if already initialized."""
        import asp.telemetry.config as config_module

        # Set initialization flag
        config_module._logfire_initialized = True

        from asp.telemetry.config import configure_logfire

        result = configure_logfire()

        assert result is True

        # Reset for next test
        config_module._logfire_initialized = False

    def test_configure_logfire_import_error(self):
        """Test Logfire returns False if import fails."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False

        # Remove logfire from modules to simulate ImportError
        with mock.patch.dict(sys.modules, {"logfire": None}):
            # This will cause ImportError when trying to import
            original_import = (
                __builtins__.__import__
                if hasattr(__builtins__, "__import__")
                else __import__
            )

            def mock_import(name, *args, **kwargs):
                if name == "logfire":
                    raise ImportError("No module named 'logfire'")
                return original_import(name, *args, **kwargs)

            with mock.patch("builtins.__import__", side_effect=mock_import):
                import importlib

                importlib.reload(config_module)
                result = config_module.configure_logfire()

                assert result is False

        config_module._logfire_initialized = False

    def test_configure_logfire_uses_environment_vars(self):
        """Test Logfire configuration uses environment variables."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False

        mock_logfire = mock.MagicMock()
        with mock.patch.dict(
            os.environ,
            {
                "ASP_ENVIRONMENT": "production",
                "ASP_VERSION": "1.2.3",
                "LOGFIRE_SEND": "false",
                "ASP_TELEMETRY_CONSOLE": "true",
            },
        ):
            with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
                from asp.telemetry.config import configure_logfire

                result = configure_logfire(service_name="my-service")

                assert result is True
                mock_logfire.configure.assert_called_once()
                call_kwargs = mock_logfire.configure.call_args[1]
                assert call_kwargs["service_name"] == "my-service"
                assert call_kwargs["environment"] == "production"
                assert call_kwargs["service_version"] == "1.2.3"
                assert call_kwargs["send_to_logfire"] is False
                assert call_kwargs["console"] is True

        config_module._logfire_initialized = False


class TestConfigurePydanticPlugin:
    """Tests for configure_pydantic_plugin function."""

    def test_configure_pydantic_plugin_success(self):
        """Test successful Pydantic plugin configuration."""
        mock_logfire = mock.MagicMock()
        mock_logfire.PydanticPlugin = mock.MagicMock(return_value="plugin")

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_pydantic_plugin

            result = configure_pydantic_plugin(record="all")

            assert result is True
            mock_logfire.configure.assert_called_once()


class TestConfigureAnthropicInstrumentation:
    """Tests for configure_anthropic_instrumentation function."""

    def test_configure_anthropic_success(self):
        """Test successful Anthropic instrumentation."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_anthropic = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_anthropic_instrumentation

            result = configure_anthropic_instrumentation()

            assert result is True
            mock_logfire.instrument_anthropic.assert_called_once()

    def test_configure_anthropic_no_method(self):
        """Test Anthropic returns False if method not available."""
        mock_logfire = mock.MagicMock(spec=[])  # No methods

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_anthropic_instrumentation

            result = configure_anthropic_instrumentation()

            assert result is False

    def test_configure_anthropic_exception(self):
        """Test Anthropic handles exceptions gracefully."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_anthropic.side_effect = Exception("API error")

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_anthropic_instrumentation

            result = configure_anthropic_instrumentation()

            assert result is False


class TestConfigureOpenAIInstrumentation:
    """Tests for configure_openai_instrumentation function."""

    def test_configure_openai_success(self):
        """Test successful OpenAI instrumentation."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_openai = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_openai_instrumentation

            result = configure_openai_instrumentation()

            assert result is True
            mock_logfire.instrument_openai.assert_called_once()

    def test_configure_openai_no_method(self):
        """Test OpenAI returns False if method not available."""
        mock_logfire = mock.MagicMock(spec=[])

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_openai_instrumentation

            result = configure_openai_instrumentation()

            assert result is False

    def test_configure_openai_exception(self):
        """Test OpenAI handles exceptions gracefully."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_openai.side_effect = Exception("API error")

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_openai_instrumentation

            result = configure_openai_instrumentation()

            assert result is False


class TestConfigureHTTPXInstrumentation:
    """Tests for configure_httpx_instrumentation function."""

    def test_configure_httpx_success(self):
        """Test successful HTTPX instrumentation."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_httpx = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_httpx_instrumentation

            result = configure_httpx_instrumentation()

            assert result is True
            mock_logfire.instrument_httpx.assert_called_once()

    def test_configure_httpx_no_method(self):
        """Test HTTPX returns False if method not available."""
        mock_logfire = mock.MagicMock(spec=[])

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_httpx_instrumentation

            result = configure_httpx_instrumentation()

            assert result is False

    def test_configure_httpx_exception(self):
        """Test HTTPX handles exceptions gracefully."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_httpx.side_effect = Exception("API error")

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import configure_httpx_instrumentation

            result = configure_httpx_instrumentation()

            assert result is False


class TestInstrumentAllLLMProviders:
    """Tests for instrument_all_llm_providers function."""

    def test_instrument_all_providers(self):
        """Test instrumenting all LLM providers."""
        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_anthropic = mock.MagicMock()
        mock_logfire.instrument_openai = mock.MagicMock()
        mock_logfire.instrument_httpx = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import instrument_all_llm_providers

            result = instrument_all_llm_providers()

            assert result["anthropic"] is True
            assert result["openai"] is True
            assert result["httpx"] is True


class TestInitializeTelemetry:
    """Tests for initialize_telemetry function."""

    def test_initialize_with_logfire(self):
        """Test initialization with logfire provider."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_anthropic = mock.MagicMock()
        mock_logfire.instrument_openai = mock.MagicMock()
        mock_logfire.instrument_httpx = mock.MagicMock()

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "logfire"}):
            with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
                from asp.telemetry.config import initialize_telemetry

                result = initialize_telemetry(service_name="test")

                assert result["provider"] == "logfire"
                assert result["logfire_configured"] is True
                assert "anthropic" in result["llm_instrumentation"]

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

    def test_initialize_with_langfuse(self):
        """Test initialization with langfuse provider."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "langfuse"}):
            from asp.telemetry.config import initialize_telemetry

            result = initialize_telemetry()

            assert result["provider"] == "langfuse"
            assert result["logfire_configured"] is False
            assert result["llm_instrumentation"] == {}

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

    def test_initialize_with_none(self):
        """Test initialization with none provider."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "none"}):
            from asp.telemetry.config import initialize_telemetry

            result = initialize_telemetry()

            assert result["provider"] == "none"
            assert result["logfire_configured"] is False

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

    def test_initialize_without_llm_instrumentation(self):
        """Test initialization without LLM instrumentation."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

        mock_logfire = mock.MagicMock()

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "logfire"}):
            with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
                from asp.telemetry.config import initialize_telemetry

                result = initialize_telemetry(instrument_llm=False)

                assert result["provider"] == "logfire"
                assert result["llm_instrumentation"] == {}

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False


class TestEnsureLLMInstrumentation:
    """Tests for ensure_llm_instrumentation function."""

    def test_already_instrumented(self):
        """Test returns True if already instrumented."""
        import asp.telemetry.config as config_module

        config_module._llm_instrumentation_done = True

        from asp.telemetry.config import ensure_llm_instrumentation

        result = ensure_llm_instrumentation()

        assert result is True

        config_module._llm_instrumentation_done = False

    def test_not_logfire_provider(self):
        """Test returns False if not using logfire."""
        import asp.telemetry.config as config_module

        config_module._llm_instrumentation_done = False

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "langfuse"}):
            from asp.telemetry.config import ensure_llm_instrumentation

            result = ensure_llm_instrumentation()

            assert result is False

        config_module._llm_instrumentation_done = False

    def test_logfire_provider_instruments(self):
        """Test instruments LLM providers with logfire."""
        import asp.telemetry.config as config_module

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False

        mock_logfire = mock.MagicMock()
        mock_logfire.instrument_anthropic = mock.MagicMock()
        mock_logfire.instrument_openai = mock.MagicMock()
        mock_logfire.instrument_httpx = mock.MagicMock()

        with mock.patch.dict(os.environ, {"ASP_TELEMETRY_PROVIDER": "logfire"}):
            with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
                from asp.telemetry.config import ensure_llm_instrumentation

                result = ensure_llm_instrumentation()

                assert result is True

        config_module._logfire_initialized = False
        config_module._llm_instrumentation_done = False


class TestIsLogfireAvailable:
    """Tests for is_logfire_available function."""

    def test_logfire_available(self):
        """Test returns True when logfire is importable."""
        mock_logfire = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"logfire": mock_logfire}):
            from asp.telemetry.config import is_logfire_available

            result = is_logfire_available()

            assert result is True


class TestIsLangfuseAvailable:
    """Tests for is_langfuse_available function."""

    def test_langfuse_available(self):
        """Test returns True when langfuse is importable."""
        mock_langfuse_module = mock.MagicMock()
        mock_langfuse_module.Langfuse = mock.MagicMock()

        with mock.patch.dict(sys.modules, {"langfuse": mock_langfuse_module}):
            from asp.telemetry.config import is_langfuse_available

            result = is_langfuse_available()

            assert result is True
