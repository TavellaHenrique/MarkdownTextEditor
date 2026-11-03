import unicodedata

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from markdown_editor.typography import (
    EDITOR_DEFAULT_FONT_SIZE,
    EDITOR_FONT_SIZE_STEP,
    EDITOR_MAX_FONT_SIZE,
    EDITOR_MIN_FONT_SIZE,
    create_editor_font,
)


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

    def update_font(self):
        """Synchronize the gutter font with the editor font."""
        self.setFont(self.editor.font())
        self.update()


class CodeEditor(QPlainTextEdit):
    """Text editor with a line number gutter."""

    MIN_FONT_SIZE = EDITOR_MIN_FONT_SIZE
    MAX_FONT_SIZE = EDITOR_MAX_FONT_SIZE
    FONT_SIZE_STEP = EDITOR_FONT_SIZE_STEP

    @property
    def match_count(self) -> int:
        """Return the total number of search occurrences."""
        return len(self._search_matches)

    @property
    def current_match_number(self) -> int:
        """Return the one-based index of the active occurrence."""
        if self._current_match_index < 0:
            return 0

        return self._current_match_index + 1

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize the editor font size.
        self._default_font_size = EDITOR_DEFAULT_FONT_SIZE
        self._current_font_size = self._default_font_size

        # Apply the default monospaced font.
        self.setFont(create_editor_font())

        self.line_number_area = LineNumberArea(self)

        self._gutter_background = QColor("#eeeeee")
        self._gutter_foreground = QColor("#666666")

        # Initialize search state.
        self._search_matches = []
        self._current_match_index = -1
        self._highlight_all_matches = False

        # Connect document and viewport events.
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        # Initialize the gutter width.
        self.update_line_number_area_width()

        # Initialize default search highlight colors.
        self._search_highlight_color = QColor("#808080")
        self._current_match_color = QColor("#686868")

        self._current_line_background = QColor("#f1f5f9")
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.line_number_area.update)

        self.highlight_current_line()

    def set_search_colors(self, highlight_color, current_match_color):
        """Update search highlight colors according to the selected theme."""
        self._search_highlight_color = QColor(highlight_color)
        self._current_match_color = QColor(current_match_color)

        self._update_extra_selections()

    def search_text(
        self,
        search_text: str,
        case_sensitive: bool = False,
        accent_sensitive: bool = True,
        highlight_all: bool = False,
        preferred_selection: tuple[int, int] | None = None,
    ) -> int:
        """Find all occurrences of the requested text."""

        self._search_matches.clear()
        self._current_match_index = -1
        self._highlight_all_matches = highlight_all

        if not search_text:
            self._update_extra_selections()
            return 0

        document_text = self.toPlainText()

        normalized_document, position_map = self._normalize_search_text(
            document_text,
            case_sensitive,
            accent_sensitive,
        )

        normalized_query, _ = self._normalize_search_text(
            search_text,
            case_sensitive,
            accent_sensitive,
        )

        if not normalized_query:
            self._update_extra_selections()
            return 0

        # Find every occurrence in the normalized document.
        search_position = 0

        while True:
            match_position = normalized_document.find(
                normalized_query,
                search_position,
            )

            if match_position == -1:
                break

            match_end = match_position + len(normalized_query)

            original_start = position_map[match_position][0]
            original_end = position_map[match_end - 1][1]

            self._search_matches.append((original_start, original_end))

            # Advance by one character to allow overlapping matches.
            search_position = match_position + 1

        if self._search_matches:
            # Preserve the requested occurrence when it still exists.
            if preferred_selection in self._search_matches:
                self._current_match_index = self._search_matches.index(
                    preferred_selection
                )
            else:
                self._current_match_index = 0

            self._select_current_match()

        self._update_extra_selections()

        return len(self._search_matches)

    def find_next(self) -> bool:
        """Select the next search occurrence."""

        if not self._search_matches:
            return False

        self._current_match_index = (self._current_match_index + 1) % len(
            self._search_matches
        )

        self._select_current_match()
        self._update_extra_selections()

        return True

    def find_previous(self) -> bool:
        """Select the previous search occurrence."""

        if not self._search_matches:
            return False

        self._current_match_index = (self._current_match_index - 1) % len(
            self._search_matches
        )

        self._select_current_match()
        self._update_extra_selections()

        return True

    def _select_current_match(self):
        """Select the currently active search occurrence."""

        if self._current_match_index < 0:
            return

        start, end = self._search_matches[self._current_match_index]

        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    @staticmethod
    def _normalize_search_text(
        text: str,
        case_sensitive: bool,
        accent_sensitive: bool,
    ) -> tuple[str, list[tuple[int, int]]]:
        """Normalize text while preserving original character positions."""

        normalized_text = []
        position_map = []
        source_position = 0

        for character in text:
            # Decompose characters only when accent sensitivity is disabled.
            if accent_sensitive:
                normalized_character = character
            else:
                normalized_character = unicodedata.normalize(
                    "NFD",
                    character,
                )

                normalized_character = "".join(
                    char
                    for char in normalized_character
                    if unicodedata.category(char) != "Mn"
                )

            if not case_sensitive:
                normalized_character = normalized_character.casefold()

            # Preserve original UTF-16 positions used by QTextCursor.
            character_length = len(character.encode("utf-16-le")) // 2

            for normalized_char in normalized_character:
                normalized_text.append(normalized_char)
                position_map.append(
                    (source_position, source_position + character_length)
                )

            source_position += character_length

        return "".join(normalized_text), position_map

    def set_current_line_color(self, color):
        """Update the current line highlight color"""

        self._current_line_background = QColor(color)
        self.highlight_current_line()

    def highlight_current_line(self):
        """Refresh the current line and search highlights"""

        self._update_extra_selections()

    def _update_extra_selections(self):
        """Combine current line and search occurrence highlights"""

        selections = []

        # Highlight the current editor line.
        line_selection = QTextEdit.ExtraSelection()
        line_selection.format.setBackground(self._current_line_background)
        line_selection.format.setProperty(
            QTextFormat.Property.FullWidthSelection,
            True,
        )

        line_selection.cursor = self.textCursor()
        line_selection.cursor.clearSelection()

        selections.append(line_selection)

        # Highlight all search occurrences when enabled.
        if self._highlight_all_matches:
            for start, end in self._search_matches:
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(self._search_highlight_color)

                selection.cursor = QTextCursor(self.document())
                selection.cursor.setPosition(start)
                selection.cursor.setPosition(
                    end,
                    QTextCursor.MoveMode.KeepAnchor,
                )

                selections.append(selection)

        # Highlight the active occurrence with a distinct color.
        if self._current_match_index >= 0:
            start, end = self._search_matches[self._current_match_index]

            current_selection = QTextEdit.ExtraSelection()
            current_selection.format.setBackground(self._current_match_color)

            current_selection.cursor = QTextCursor(self.document())
            current_selection.cursor.setPosition(start)
            current_selection.cursor.setPosition(
                end,
                QTextCursor.MoveMode.KeepAnchor,
            )

            selections.append(current_selection)

        self.setExtraSelections(selections)

    def line_number_area_width(self):
        """Calculate the required width for line numbers."""
        digits = len(str(max(1, self.blockCount())))
        font_metrics = self.line_number_area.fontMetrics()
        digit_width = font_metrics.horizontalAdvance("9")

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
        painter.setFont(self.line_number_area.font())

        font_metrics = painter.fontMetrics()

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
                        font_metrics.height(),
                        self._current_line_background,
                    )
                    painter.setPen(self._gutter_foreground)
                else:
                    painter.setPen(self._gutter_foreground)

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 6,
                    font_metrics.height(),
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

    def increase_font_size(self):
        """Increase the editor font size."""
        new_size = min(
            self._current_font_size + self.FONT_SIZE_STEP,
            self.MAX_FONT_SIZE,
        )
        self._set_font_size(new_size)

    def decrease_font_size(self):
        """Decrease the editor font size."""
        new_size = max(
            self._current_font_size - self.FONT_SIZE_STEP,
            self.MIN_FONT_SIZE,
        )
        self._set_font_size(new_size)

    def reset_font_size(self):
        """Restore the default editor font size."""
        self._set_font_size(self._default_font_size)

    def _set_font_size(self, size):
        """Apply a font size and update the line number area."""
        self._current_font_size = max(
            self.MIN_FONT_SIZE,
            min(size, self.MAX_FONT_SIZE),
        )

        font = self.font()
        font.setPointSize(round(self._current_font_size))

        self.setFont(font)

        # Synchronize the gutter font with the editor.
        self.line_number_area.update_font()

        # Recalculate the gutter dimensions.
        self.update_line_number_area_width()
        self.line_number_area.update()
