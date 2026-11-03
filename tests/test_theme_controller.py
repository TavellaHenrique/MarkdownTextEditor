import pytest

from markdown_editor.theme_controller import ThemeController
from markdown_editor.themes import DARK_THEME, LIGHT_THEME


@pytest.fixture
def controller():
    """Create a theme controller instance."""
    return ThemeController()


def test_initial_theme(controller):
    """Initialize with the dark theme by default."""
    assert controller.current_theme_name == "dark"
    assert controller.current_theme == DARK_THEME


def test_available_themes(controller):
    """Return all registered theme names."""
    assert controller.available_themes == ("light", "dark")


def test_set_theme(controller):
    """Change the selected theme."""
    theme = controller.set_theme("light")

    assert theme == LIGHT_THEME
    assert controller.current_theme_name == "light"


def test_unknown_theme(controller):
    """Reject themes that are not registered."""
    with pytest.raises(ValueError):
        controller.set_theme("unknown")


def test_custom_theme_registry():
    """Allow a custom theme registry."""
    themes = {"custom": LIGHT_THEME}

    controller = ThemeController(
        themes=themes,
        initial_theme="custom",
    )

    assert controller.available_themes == ("custom",)
    assert controller.current_theme == LIGHT_THEME
