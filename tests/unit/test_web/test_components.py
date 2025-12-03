"""
Unit tests for web UI components.

Tests reusable UI components used across persona dashboards.
"""


class TestThemeToggle:
    """Test the theme_toggle component."""

    def test_returns_button_element(self):
        """Test theme_toggle returns a button element."""
        from asp.web.components import theme_toggle

        button = theme_toggle()

        # Should be a Button element (FT component)
        assert button is not None
        # The button tag should be 'button'
        assert button.tag == "button"

    def test_has_theme_toggle_class(self):
        """Test theme_toggle has the correct CSS class."""
        from asp.web.components import theme_toggle

        button = theme_toggle()

        # Check attributes
        assert "class" in button.attrs
        assert "theme-toggle" in button.attrs["class"]

    def test_has_onclick_handler(self):
        """Test theme_toggle has onclick handler."""
        from asp.web.components import theme_toggle

        button = theme_toggle()

        assert "onclick" in button.attrs
        # Check for key JavaScript elements
        assert "localStorage" in button.attrs["onclick"]
        assert "data-theme" in button.attrs["onclick"]

    def test_contains_child_spans(self):
        """Test theme_toggle contains icon and text spans."""
        from asp.web.components import theme_toggle

        button = theme_toggle()

        # Should have 2 children (icon span and text span)
        assert len(button.children) == 2
