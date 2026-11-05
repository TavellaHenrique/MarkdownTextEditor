from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar

from markdown_editor.code_editor import CodeEditor
from markdown_editor.find_bar import FindBar


class SearchController:
    """Coordinate text search and navigation between occurrences."""

    MESSAGE_TIMEOUT = 5000

    def __init__(
        self,
        editor: CodeEditor,
        find_bar: FindBar,
        status_bar: QStatusBar,
    ):
        """Initialize search dependencies and connect signals."""
        self._editor = editor
        self._find_bar = find_bar
        self._status_bar = status_bar

        self._connect_signals()

    def _connect_signals(self):
        """Connect search bar signals to controller methods."""
        self._find_bar.search_text_changed.connect(self.update_search)
        self._find_bar.highlight_all_changed.connect(self.update_search)
        self._find_bar.case_sensitive_changed.connect(self.update_search)
        self._find_bar.accent_sensitive_changed.connect(self.update_search)

        self._find_bar.next_requested.connect(self.find_next)
        self._find_bar.previous_requested.connect(self.find_previous)
        self._find_bar.close_requested.connect(self.clear_search)

    def update_search(
        self,
        _value=None,
        preferred_selection=None,
    ):
        """Execute the search and update the occurrence indicator."""
        if preferred_selection is None:
            cursor = self._editor.textCursor()

            if cursor.hasSelection():
                preferred_selection = (
                    cursor.selectionStart(),
                    cursor.selectionEnd(),
                )

        search_text = self._find_bar.search_input.text()

        match_count = self._editor.search_text(
            search_text,
            case_sensitive=self._find_bar.case_sensitive_action.isChecked(),
            accent_sensitive=self._find_bar.accent_sensitive_action.isChecked(),
            highlight_all=self._find_bar.highlight_all_action.isChecked(),
            preferred_selection=preferred_selection,
        )

        self._update_match_indicator()

        if search_text and match_count == 0:
            self._status_bar.showMessage(
                "No results found",
                self.MESSAGE_TIMEOUT,
            )
        elif search_text:
            self._status_bar.showMessage(
                f"{match_count} matches found",
                self.MESSAGE_TIMEOUT,
            )

    def find_next(self):
        """Navigate to the next occurrence."""
        self._editor.find_next()
        self._update_match_indicator()

    def find_previous(self):
        """Navigate to the previous occurrence."""
        self._editor.find_previous()
        self._update_match_indicator()

    def _update_match_indicator(self):
        """Refresh the current occurrence indicator."""
        self._find_bar.update_match_indicator(
            self._editor.current_match_number,
            self._editor.match_count,
        )

    def clear_search(self):
        """Clear search results and restore editor focus."""
        self._editor.search_text("")

        # Restore focus after the search bar finishes hiding.
        QTimer.singleShot(0, self._editor.setFocus)
