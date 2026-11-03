from PySide6.QtWidgets import QTextBrowser

from markdown_editor.markdown_parser import MarkdownParser
from markdown_editor.theme_controller import ThemeController
from markdown_editor.themes import build_preview_html


class PreviewController:
    """Coordinate Markdown rendering and preview updates."""

    def __init__(
        self,
        preview: QTextBrowser,
        theme_controller: ThemeController,
        parser: MarkdownParser | None = None,
    ):
        """Initialize preview dependencies."""
        self._preview = preview
        self._theme_controller = theme_controller
        self._parser = parser or MarkdownParser()

    def render_preview(self, markdown_text: str) -> str:
        """Generate themed HTML from Markdown content."""
        markdown_html = self._parser.to_html(markdown_text)
        theme = self._theme_controller.current_theme

        return build_preview_html(markdown_html, theme)

    def update_preview(self, markdown_text: str) -> None:
        """Update the preview while preserving scroll positions."""
        vertical_position = self._preview.verticalScrollBar().value()
        horizontal_position = self._preview.horizontalScrollBar().value()

        preview_html = self.render_preview(markdown_text)

        self._preview.setHtml(preview_html)

        self._preview.verticalScrollBar().setValue(vertical_position)
        self._preview.horizontalScrollBar().setValue(horizontal_position)
