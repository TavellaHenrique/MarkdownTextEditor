import pytest
from PySide6.QtWidgets import QTextBrowser

from markdown_editor.preview_controller import PreviewController
from markdown_editor.theme_controller import ThemeController


@pytest.fixture
def preview_controller(qtbot):
    """Create a preview controller with its dependencies."""
    preview = QTextBrowser()
    qtbot.addWidget(preview)

    theme_controller = ThemeController()

    controller = PreviewController(
        preview=preview,
        theme_controller=theme_controller,
    )

    return controller, preview, theme_controller


def test_update_preview_renders_markdown(preview_controller):
    """Render Markdown content as HTML."""
    controller, preview, _ = preview_controller

    controller.update_preview("# Preview Test")

    assert "<h1" in preview.toHtml()
    assert "Preview Test" in preview.toPlainText()


def test_render_preview_uses_current_theme(preview_controller):
    """Use the currently selected theme when generating HTML."""
    controller, _, theme_controller = preview_controller

    theme_controller.set_theme("light")

    preview_html = controller.render_preview("# Light Theme")

    assert "#f5f5f5" in preview_html.lower()
    assert "Light Theme" in preview_html


def test_render_preview_uses_theme_link_colors_and_hover_title(preview_controller):
    """Apply the theme colors to links and expose the hover title in the preview."""
    controller, _, theme_controller = preview_controller

    theme_controller.set_theme("dark")

    preview_html = controller.render_preview('[Docs](https://example.com "Example title")')

    assert "#8ab4f8" in preview_html.lower()
    assert "#d2e3fc" in preview_html.lower()
    assert "example title" in preview_html.lower()
    assert 'style="color:#8ab4f8' in preview_html.lower().replace(" ", "")


def test_update_preview_refreshes_content(preview_controller):
    """Replace the previous preview content."""
    controller, preview, _ = preview_controller

    controller.update_preview("# First Document")
    controller.update_preview("# Second Document")

    assert "Second Document" in preview.toPlainText()
    assert "First Document" not in preview.toPlainText()
