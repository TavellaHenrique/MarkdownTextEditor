import re

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QHelpEvent
from PySide6.QtWidgets import QTextBrowser, QToolTip

from markdown_editor.markdown_parser import MarkdownParser
from markdown_editor.theme_controller import ThemeController
from markdown_editor.themes import build_preview_html
from markdown_editor.typography import create_preview_font


class PreviewBrowser(QTextBrowser):
    """Handle hover tooltips for Markdown links without breaking Qt document navigation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tooltips = {}

    def set_html_with_tooltips(self, html: str) -> None:
        """Set preview HTML while recording link titles for hover tooltips."""
        self._tooltips = {
            href: title
            for href, title in re.findall(
                r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*title=["\']([^"\']*)["\']',
                html,
                flags=re.IGNORECASE,
            )
        }
        self.setHtml(html)

    def mouseMoveEvent(self, event):
        """Display a tooltip for hovered Markdown links using the title attribute."""
        anchor = self.anchorAt(event.pos())

        if anchor and anchor in self._tooltips:
            QToolTip.showText(event.globalPos(), self._tooltips[anchor], self)
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Open link targets in the system browser instead of trying to load them as documents."""
        anchor = self.anchorAt(event.pos())

        if anchor:
            QDesktopServices.openUrl(QUrl(anchor))
            return

        super().mousePressEvent(event)

    def event(self, event):
        """Allow the tooltip to remain visible while the mouse is over a link."""
        if event.type() == QHelpEvent.ToolTip and self.anchorAt(event.pos()):
            return True

        return super().event(event)


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
        self._preview.setFont(create_preview_font())
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

        if hasattr(self._preview, "set_html_with_tooltips"):
            self._preview.set_html_with_tooltips(preview_html)
        else:
            self._preview.setHtml(preview_html)

        self._preview.verticalScrollBar().setValue(vertical_position)
        self._preview.horizontalScrollBar().setValue(horizontal_position)
