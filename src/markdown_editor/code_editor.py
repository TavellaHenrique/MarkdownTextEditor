import re
import unicodedata

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPalette,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QInputDialog, QPlainTextEdit, QTextEdit, QWidget

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
                self._current_match_index = self._search_matches.index(preferred_selection)
            else:
                self._current_match_index = 0

            self._select_current_match()

        self._update_extra_selections()

        return len(self._search_matches)

    def find_next(self) -> bool:
        """Select the next search occurrence."""

        if not self._search_matches:
            return False

        self._current_match_index = (self._current_match_index + 1) % len(self._search_matches)

        self._select_current_match()
        self._update_extra_selections()

        return True

    def find_previous(self) -> bool:
        """Select the previous search occurrence."""

        if not self._search_matches:
            return False

        self._current_match_index = (self._current_match_index - 1) % len(self._search_matches)

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
                    char for char in normalized_character if unicodedata.category(char) != "Mn"
                )

            if not case_sensitive:
                normalized_character = normalized_character.casefold()

            # Preserve original UTF-16 positions used by QTextCursor.
            character_length = len(character.encode("utf-16-le")) // 2

            for normalized_char in normalized_character:
                normalized_text.append(normalized_char)
                position_map.append((source_position, source_position + character_length))

            source_position += character_length

        return "".join(normalized_text), position_map

    def set_current_line_color(self, color):
        """Update the current line highlight color"""

        self._current_line_background = QColor(color)
        self.highlight_current_line()

    def set_placeholder_color(self, color):
        """Apply the placeholder text color for the empty editor state."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(color))
        self.setPalette(palette)

    def highlight_current_line(self):
        """Refresh the current line and search highlights"""

        self._update_extra_selections()

    def _update_extra_selections(self):
        """Combine current line and search occurrence highlights"""

        if self.document().isEmpty():
            self.setExtraSelections([])
            return

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

        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())

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

    @staticmethod
    def _utf16_length(text: str) -> int:
        """Return the number of UTF-16 code units in a string."""
        return len(text.encode("utf-16-le")) // 2

    def _get_text_range(self, start: int, end: int) -> str:
        """Return the document text between two UTF-16 positions."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

        return cursor.selectedText().replace("\u2029", "\n")

    def _count_adjacent_markers(
        self,
        position: int,
        marker: str,
        direction: int,
    ) -> int:
        """Count consecutive Markdown markers adjacent to a position."""
        count = 0
        marker_length = self._utf16_length(marker)

        while True:
            if direction < 0:
                start = position - (count + 1) * marker_length
                end = position - count * marker_length
            else:
                start = position + count * marker_length
                end = start + marker_length

            if start < 0:
                break

            if self._get_text_range(start, end) != marker:
                break

            count += 1

        return count

    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        """Toggle Markdown formatting while preserving other emphasis."""
        cursor = self.textCursor()

        if not cursor.hasSelection():
            start = cursor.position()
            cursor.insertText(f"{prefix}{suffix}")
            cursor.setPosition(start + self._utf16_length(prefix))
            self.setTextCursor(cursor)
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selected_text = self._get_text_range(start, end)

        marker = prefix
        marker_count = len(marker)
        prefix_length = self._utf16_length(prefix)
        suffix_length = self._utf16_length(suffix)

        # Remove delimiters included in the selection itself.
        if selected_text.startswith(prefix) and selected_text.endswith(suffix):
            content = selected_text[len(prefix) : len(selected_text) - len(suffix)]

            cursor.insertText(content)
            self._select_text(
                start,
                start + self._utf16_length(content),
            )
            return

        if marker == "*":
            # Count individual asterisks to distinguish combined formatting.
            left_count = self._count_adjacent_markers(start, "*", -1)
            right_count = self._count_adjacent_markers(end, "*", 1)

            is_formatted = left_count == right_count and left_count in {marker_count, 3}
        else:
            # Count complete strikethrough marker pairs.
            left_count = self._count_adjacent_markers(
                start,
                marker,
                -1,
            )
            right_count = self._count_adjacent_markers(
                end,
                marker,
                1,
            )

            is_formatted = left_count == right_count == 1

        if is_formatted:
            # Remove only the requested formatting markers.
            cursor.setPosition(start - prefix_length)
            cursor.setPosition(
                end + suffix_length,
                QTextCursor.MoveMode.KeepAnchor,
            )
            cursor.insertText(selected_text)

            self._select_text(
                start - prefix_length,
                start - prefix_length + self._utf16_length(selected_text),
            )
            return

        # Apply formatting while preserving existing delimiters.
        cursor.insertText(f"{prefix}{selected_text}{suffix}")

        self._select_text(
            start + prefix_length,
            start + prefix_length + self._utf16_length(selected_text),
        )

    def _has_exact_wrapping(
        self,
        start: int,
        end: int,
        prefix: str,
        suffix: str,
    ) -> bool:
        """Check whether the selection has exactly the requested delimiters."""
        prefix_length = self._utf16_length(prefix)
        suffix_length = self._utf16_length(suffix)

        if start < prefix_length:
            return False

        if self._get_text_range(start - prefix_length, start) != prefix:
            return False

        if self._get_text_range(end, end + suffix_length) != suffix:
            return False

        # Avoid confusing bold delimiters with italic delimiters.
        marker = prefix[-1]

        if start > prefix_length:
            if (
                self._get_text_range(
                    start - prefix_length - 1,
                    start - prefix_length,
                )
                == marker
            ):
                return False

        if (
            self._get_text_range(
                end + suffix_length,
                end + suffix_length + 1,
            )
            == marker
        ):
            return False

        return True

    def _select_text(self, start: int, end: int) -> None:
        """Select a document range using valid UTF-16 positions."""
        document_length = self._utf16_length(self.toPlainText())

        start = max(0, min(start, document_length))
        end = max(start, min(end, document_length))

        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

        self.setTextCursor(cursor)

    def format_bold(self) -> None:
        """Apply Markdown bold formatting."""
        self._wrap_selection("**", "**")

    def format_italic(self) -> None:
        """Apply Markdown italic formatting."""
        self._wrap_selection("*", "*")

    def insert_link(self) -> None:
        """Insert a Markdown link using the current selection."""
        cursor = self.textCursor()
        start = cursor.selectionStart()
        selected_text = cursor.selectedText().replace("\u2029", "\n")

        if cursor.hasSelection():
            cursor.insertText(f"[{selected_text}](url)")

            # Select the URL placeholder for immediate editing.
            url_start = start + self._utf16_length(f"[{selected_text}](")
            url_end = url_start + self._utf16_length("url")

            cursor = QTextCursor(self.document())
            cursor.setPosition(url_start)
            cursor.setPosition(
                url_end,
                QTextCursor.MoveMode.KeepAnchor,
            )
        else:
            cursor.insertText("[text](url)")

            # Select the link text placeholder.
            cursor = QTextCursor(self.document())
            cursor.setPosition(start + 1)
            cursor.setPosition(
                start + 1 + self._utf16_length("text"),
                QTextCursor.MoveMode.KeepAnchor,
            )

        self.setTextCursor(cursor)

    def set_heading_level(self, level: int) -> None:
        """Apply a Markdown heading level to the current line."""
        if not isinstance(level, int) or isinstance(level, bool):
            raise ValueError("Heading level must be an integer.")

        if not 1 <= level <= 6:
            raise ValueError("Heading level must be between 1 and 6.")

        cursor = self.textCursor()
        block = cursor.block()
        block_text = block.text()
        original_position = cursor.positionInBlock()

        # Identify and remove an existing heading marker.
        match = re.match(r"^#{1,6}\s+", block_text)
        old_prefix_length = self._utf16_length(match.group()) if match else 0

        content = block_text[match.end() :] if match else block_text
        new_prefix = f"{'#' * level} "
        heading = f"{new_prefix}{content}"

        # Replace the entire current block.
        block_cursor = QTextCursor(block)
        block_cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        block_cursor.insertText(heading)

        # Preserve the cursor position relative to the heading content.
        content_position = max(
            0,
            original_position - old_prefix_length,
        )
        content_position = min(
            content_position,
            self._utf16_length(content),
        )

        new_position = block.position() + self._utf16_length(new_prefix) + content_position

        new_cursor = QTextCursor(self.document())
        new_cursor.setPosition(new_position)
        self.setTextCursor(new_cursor)

    def _normalize_list_item(self, line: str) -> str:
        """Remove an existing Markdown list marker from a line."""
        stripped = line.strip()
        if not stripped:
            return ""

        match = re.match(r"^(?:\d+\.|\*|-)\s*(.*)$", stripped)
        if match:
            return match.group(1).strip()

        return stripped

    def insert_ordered_list(self) -> None:
        """Insert or reformat a numbered Markdown list from the selection or prompt."""
        cursor = self.textCursor()

        if cursor.hasSelection():
            selected_text = self._get_text_range(
                cursor.selectionStart(),
                cursor.selectionEnd(),
            )
            lines = [line.rstrip() for line in selected_text.splitlines()]
            if lines and any(line.strip() for line in lines):
                normalized_lines = [
                    self._normalize_list_item(line) for line in lines if line.strip()
                ]
                if normalized_lines:
                    replacement = "\n".join(
                        f"{index}. {line}" for index, line in enumerate(normalized_lines, start=1)
                    )
                    cursor.insertText(replacement)
                    return

        item_count, confirmed = QInputDialog.getInt(
            self,
            "Ordered List",
            "How many items should the list contain?",
            3,
            1,
            100,
            1,
        )

        if not confirmed:
            return

        self._insert_list_lines(item_count, lambda index: f"{index}. ")

    def insert_unordered_list(self) -> None:
        """Insert or strip list formatting from the selection or prompt."""
        cursor = self.textCursor()

        if cursor.hasSelection():
            selected_text = self._get_text_range(
                cursor.selectionStart(),
                cursor.selectionEnd(),
            )
            lines = [line.rstrip() for line in selected_text.splitlines()]
            if lines and any(line.strip() for line in lines):
                normalized_lines = [
                    self._normalize_list_item(line) for line in lines if line.strip()
                ]
                if normalized_lines:
                    replacement = "\n".join(f"- {line}" for line in normalized_lines)
                    cursor.insertText(replacement)
                    return

        item_count, confirmed = QInputDialog.getInt(
            self,
            "Unordered List",
            "How many items?",
            3,
            1,
            100,
            1,
        )

        if not confirmed:
            return

        self._insert_list_lines(item_count, lambda _index: "- ")

    def _insert_list_lines(
        self,
        item_count: int,
        formatter: callable,
    ) -> None:
        """Insert a list using the current line content when present."""
        cursor = self.textCursor()
        block = cursor.block()
        current_text = block.text().strip()

        if current_text:
            replacement = "\n".join(
                f"{formatter(index)}{current_text}" if index == 1 else f"{formatter(index)}"
                for index in range(1, item_count + 1)
            )

            block_cursor = QTextCursor(block)
            block_cursor.movePosition(
                QTextCursor.MoveOperation.EndOfBlock,
                QTextCursor.MoveMode.KeepAnchor,
            )
            block_cursor.insertText(replacement)
            return

        cursor.insertText("\n".join(f"{formatter(index)}" for index in range(1, item_count + 1)))

    @property
    def font_size(self) -> int:
        """Return the current editor font size."""
        return self._current_font_size

    def set_font_size(self, size: int) -> None:
        """Set the editor font size."""
        if not isinstance(size, int) or isinstance(size, bool):
            raise ValueError("Font size must be an integer.")

        self._set_font_size(size)

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
