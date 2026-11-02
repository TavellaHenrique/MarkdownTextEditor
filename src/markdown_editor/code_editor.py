from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class LineNumberArea(QWidget):
    """Widget responsible for displaying editor line numbers."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        """Return the preferred size of the line number area."""
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """Delegate line number painting to the editor."""
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Text editor with a line number gutter."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.line_number_area = LineNumberArea(self)

        self._gutter_background = QColor("#eeeeee")
        self._gutter_foreground = QColor("#666666")

        # Connect document and viewport events.
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        # Initialize the gutter width.
        self.update_line_number_area_width()

        self._current_line_background = QColor("#f1f5f9")
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.line_number_area.update)

        self.highlight_current_line()

    def set_current_line_color(self, color):
        """Update the current line highlight color"""

        self._current_line_background = QColor(color)
        self.highlight_current_line()

    def highlight_current_line(self):
        """Highlight the line containing the text cursor"""

        selection = QTextEdit.ExtraSelection()

        selection.format.setBackground(self._current_line_background)
        selection.format.setProperty(
            QTextFormat.Property.FullWidthSelection,
            True,
        )

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections([selection])

    def line_number_area_width(self):
        """Calculate the required width for line numbers."""
        digits = len(str(max(1, self.blockCount())))
        digit_width = self.fontMetrics().horizontalAdvance("9")

        return 12 + digit_width * digits

    def update_line_number_area_width(self, _block_count=0):
        """Reserve space for the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the gutter when the editor viewport changes."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                rect.y(),
                self.line_number_area.width(),
                rect.height(),
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        """Position the gutter when the editor is resized."""
        super().resizeEvent(event)

        content_rect = self.contentsRect()

        self.line_number_area.setGeometry(
            QRect(
                content_rect.left(),
                content_rect.top(),
                self.line_number_area_width(),
                content_rect.height(),
            )
        )

    def line_number_area_paint_event(self, event):
        """Draw line numbers for all visible text blocks."""
        painter = QPainter(self.line_number_area)

        painter.fillRect(
            event.rect(),
            self._gutter_background,
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )

        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = str(block_number + 1)

                # Draw the line number with a highlighted background when selected.
                if block_number == self.textCursor().blockNumber():
                    painter.fillRect(
                        0,
                        top,
                        self.line_number_area.width(),
                        self.fontMetrics().height(),
                        self._current_line_background,
                    )
                    painter.setPen(self._gutter_foreground)
                else:
                    painter.setPen(self._gutter_foreground)

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    line_number,
                )

            block = block.next()
            block_number += 1

            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())

    def set_line_number_colors(self, background, foreground):
        """Update the gutter colors according to the selected theme."""
        self._gutter_background = QColor(background)
        self._gutter_foreground = QColor(foreground)

        self.line_number_area.update()
