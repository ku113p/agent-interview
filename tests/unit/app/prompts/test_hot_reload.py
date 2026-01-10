import time
from unittest.mock import patch

from src.app.prompts.renderer import PromptRenderer


def test_hot_reload_enabled(tmp_path):
    """Verify that templates reload when modified if configured."""
    # Create a dummy template in the temp dir
    template_dir = tmp_path / "prompts"
    template_dir.mkdir()
    template_file = template_dir / "test.j2"
    template_file.write_text("Hello {{ name }} v1")

    # Initialize renderer pointing to temp dir
    # We patch settings to ensure we are in "local" environment
    # (or whatever triggers hot reload)
    with patch("src.app.prompts.renderer.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "local"

        # Initialize renderer
        renderer = PromptRenderer(templates_dir=template_dir)

        # First render
        result1 = renderer.render("test.j2", name="World")
        assert result1 == "Hello World v1"

        # Modify file
        # Sleep briefly to ensure mtime changes (fs resolution)
        time.sleep(0.1)
        template_file.write_text("Hello {{ name }} v2")

        # Second render - should reflect change
        result2 = renderer.render("test.j2", name="World")
        assert result2 == "Hello World v2"


def test_hot_reload_disabled_in_prod(tmp_path):
    """Verify that templates DO NOT reload in production."""
    template_dir = tmp_path / "prompts"
    template_dir.mkdir()
    template_file = template_dir / "test.j2"
    template_file.write_text("Hello {{ name }} v1")

    with patch("src.app.prompts.renderer.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"

        renderer = PromptRenderer(templates_dir=template_dir)

        result1 = renderer.render("test.j2", name="World")
        assert result1 == "Hello World v1"

        time.sleep(0.1)
        template_file.write_text("Hello {{ name }} v2")

        # Second render - should still be v1
        result2 = renderer.render("test.j2", name="World")
        assert result2 == "Hello World v1"
