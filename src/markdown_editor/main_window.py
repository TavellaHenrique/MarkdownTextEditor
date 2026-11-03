from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QTextBrowser,
)

from markdown_editor.code_editor import CodeEditor
from markdown_editor.file_manager import FileManager
from markdown_editor.find_bar import FindBar
from markdown_editor.markdown_parser import MarkdownParser
from markdown_editor.themes import (
    THEMES,
    build_preview_html,
    load_application_stylesheet,
)


class MainWindow(QMainWindow):
    """Main application window"""

    INITIAL_WIDTH = 1000
    INITIAL_HEIGHT = 500
    MESSAGE_TIMEOUT = 5000  # ms

    def __init__(self):
        super().__init__()

        # Initialize the File Manager
        self.current_file_path = None
        self.file_manager = FileManager()

        # Initialize the Markdown parser
        self.markdown_parser = MarkdownParser()

        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        self.current_theme = "dark"

        self._create_editor()
        self._create_find_bar()
        self._create_preview()
        self._create_splitter()
        self._create_menu_bar()
        self._create_status_bar()
        self._update_window_title()
        self._apply_theme()

    def _create_editor(self):
        """Create the Markdown text editor"""

        self.editor = CodeEditor()
        self.editor.setPlaceholderText("Out of words?")

        # Send a signal when changes on the text are detected
        self.editor.textChanged.connect(self._update_preview)

        # Send a signal when document changes
        self.editor.document().modificationChanged.connect(self._update_window_title)

    def _create_find_bar(self):
        """Create and configure the floating search bar."""

        self.find_bar = FindBar(self.editor)

        # Connect search navigation signals.
        self.find_bar.next_requested.connect(self._find_next)
        self.find_bar.previous_requested.connect(self._find_previous)

        # Connect search input and option signals.
        self.find_bar.search_text_changed.connect(self._update_search)
        self.find_bar.highlight_all_changed.connect(self._update_search)
        self.find_bar.case_sensitive_changed.connect(self._update_search)
        self.find_bar.accent_sensitive_changed.connect(self._update_search)

        # Observe editor resizing to keep the search bar positioned.
        self.editor.installEventFilter(self)

        # Clear search highlights and restore editor focus when closing.
        self.find_bar.close_requested.connect(self._clear_search)

    def _update_search(self, _value=None, preferred_selection=None):
        """Execute the search and update the occurrence indicator."""

        if preferred_selection is None:
            # Preserve the current editor selection when it remains a valid match.
            cursor = self.editor.textCursor()

            if cursor.hasSelection():
                preferred_selection = (
                    cursor.selectionStart(),
                    cursor.selectionEnd(),
                )

        search_text = self.find_bar.search_input.text()

        match_count = self.editor.search_text(
            search_text,
            case_sensitive=self.find_bar.case_sensitive_action.isChecked(),
            accent_sensitive=self.find_bar.accent_sensitive_action.isChecked(),
            highlight_all=self.find_bar.highlight_all_action.isChecked(),
            preferred_selection=preferred_selection,
        )

        self.find_bar.update_match_indicator(
            self.editor.current_match_number,
            match_count,
        )

        if search_text and match_count == 0:
            self.statusBar().showMessage(
                "No results found",
                self.MESSAGE_TIMEOUT,
            )
        elif search_text:
            self.statusBar().showMessage(
                f"{match_count} matches found",
                self.MESSAGE_TIMEOUT,
            )

    def _clear_search(self):
        """Clear search results and restore editor focus."""

        self.editor.search_text("")
        self.editor.setFocus()

    def _create_preview(self):
        """Create the HTML preview"""

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

    def _create_splitter(self):
        """Arrange the editor and preview horizontally"""

        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([self.width() / 2, self.width() / 2])

        self.setCentralWidget(splitter)

    def _create_menu_bar(self):
        """Create the application menu bar"""

        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()

    def _create_file_menu(self):
        """Create file menu on Menu Bar"""

        file_menu = self.menuBar().addMenu("File")
        actions = [
            ("Open", "Ctrl+O", self._open_file),
            ("Save", "Ctrl+S", self._save_file),
            ("Save As", "Ctrl+Shift+S", self._save_file_as),
        ]

        self._bind_actions_to_menu(actions, file_menu)

    def _create_edit_menu(self):
        """Create edit menu on Menu Bar"""

        edit_menu = self.menuBar().addMenu("Edit")
        actions = [
            ("Undo", "Ctrl+Z", self.editor.undo),
            ("Redo", "Ctrl+Y", self.editor.redo),
            ("Cut", "Ctrl+X", self.editor.cut),
            ("Copy", "Ctrl+C", self.editor.copy),
            ("Paste", "Ctrl+V", self.editor.paste),
            ("Select All", "Ctrl+A", self.editor.selectAll),
            ("Find", "Ctrl+F", self._show_find_bar),
        ]

        self._bind_actions_to_menu(actions, edit_menu)

    def _create_view_menu(self):
        """Create view menu on Menu Bar"""

        view_menu = self.menuBar().addMenu("View")

        preview_action = QAction("Show Preview", self)
        preview_action.setShortcut("Ctrl+P")
        preview_action.setCheckable(True)
        preview_action.setChecked(True)
        preview_action.toggled.connect(self.preview.setVisible)

        view_menu.addAction(preview_action)

        self.theme_action = QAction("Dark Theme", self)
        self.theme_action.setShortcut("Ctrl+Shift+T")
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(True)
        self.theme_action.toggled.connect(self._toggle_theme)

        view_menu.addAction(self.theme_action)

        view_menu.addSeparator()

        font_actions = [
            ("Increase Font Size", "Ctrl+=", self.editor.increase_font_size),
            ("Decrease Font Size", "Ctrl+-", self.editor.decrease_font_size),
            ("Reset Font Size", "Ctrl+0", self.editor.reset_font_size),
        ]

        self._bind_actions_to_menu(font_actions, view_menu)

    def _bind_actions_to_menu(self, actions: list, menu: QMenu):
        for text, shortcut, callback in actions:
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            menu.addAction(action)

    def _create_status_bar(self):
        """Create the application status bar"""

        self.editor.cursorPositionChanged.connect(self._update_cursor_position)

        self._update_cursor_position()

    def _update_cursor_position(self):
        """Display the current cursor position"""

        cursor = self.editor.textCursor()

        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock() + 1

        self.statusBar().showMessage(f"Line: {line} | Column: {column}")

    def _apply_theme(self):
        """Apply the selected application theme."""
        theme = THEMES[self.current_theme]

        self.setStyleSheet(load_application_stylesheet(theme))

        self.editor.set_line_number_colors(
            theme.gutter_background,
            theme.gutter_foreground,
        )
        self.editor.set_current_line_color(
            theme.current_line_background,
        )

        self._update_preview()

    def _toggle_theme(self, checked):
        """Switch between light and dark themes"""

        self.current_theme = "dark" if checked else "light"
        self._apply_theme()

    def _update_preview(self):
        """Update the HTML preview using the current Markdown text"""

        vertical_position = self.preview.verticalScrollBar().value()
        horizontal_position = self.preview.horizontalScrollBar().value()

        markdown_text = self.editor.toPlainText()
        markdown_html = self.markdown_parser.to_html(markdown_text)

        theme = THEMES[self.current_theme]
        preview_html = build_preview_html(markdown_html, theme)

        self.preview.setHtml(preview_html)

        # Restore previous scroll position
        self.preview.verticalScrollBar().setValue(vertical_position)
        self.preview.horizontalScrollBar().setValue(horizontal_position)

    def _update_window_title(self, modified=False):
        """Update the current window title with the file name and modification state"""

        if self.current_file_path:
            file_name = self.current_file_path.name
        else:
            file_name = "Untitled"

        modified_marker = "*" if modified else ""

        self.setWindowTitle(f"{modified_marker}{file_name} - Markdown Text Editor")

    def _show_find_bar(self, _checked=False):
        """Display the search bar and search the selected text."""

        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()

        preferred_selection = None

        if cursor.hasSelection():
            preferred_selection = (
                cursor.selectionStart(),
                cursor.selectionEnd(),
            )

        if self.find_bar.isVisible():
            if selected_text:
                # Update the query without triggering an intermediate search.
                self.find_bar.search_input.blockSignals(True)
                self.find_bar.search_input.setText(selected_text)
                self.find_bar.search_input.blockSignals(False)

                self.find_bar.search_input.selectAll()
                self._update_search(preferred_selection=preferred_selection)

            self.find_bar.search_input.setFocus()

        else:
            self.find_bar.show_bar(selected_text)
            self._update_search(preferred_selection=preferred_selection)

        self._position_find_bar()

    def _position_find_bar(self):
        """Position the search bar in the editor's upper-right corner."""

        self.find_bar.adjustSize()

        x_position = max(
            8,
            self.editor.width() - self.find_bar.width() - 12,
        )

        self.find_bar.move(x_position, 12)
        self.find_bar.raise_()

    def _find_next(self):
        """Navigate to the next occurrence and update the indicator."""

        self.editor.find_next()

        self.find_bar.update_match_indicator(
            self.editor.current_match_number,
            self.editor.match_count,
        )

    def _find_previous(self):
        """Navigate to the previous occurrence and update the indicator."""

        self.editor.find_previous()

        self.find_bar.update_match_indicator(
            self.editor.current_match_number,
            self.editor.match_count,
        )

    def eventFilter(self, watched, event):
        """Keep the search bar positioned when the editor is resized."""

        if (
            watched is self.editor
            and event.type() == QEvent.Type.Resize
            and self.find_bar.isVisible()
        ):
            self._position_find_bar()

        return super().eventFilter(watched, event)

    def _confirm_save_changes(self) -> bool:
        """Ask whether unsaved changes should be saved or discarded"""

        if not self.editor.document().isModified():
            return True

        answer = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "This document has unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Save:
            return self._save_file()

        return answer == QMessageBox.StandardButton.Discard

    def _open_file(self):
        """Open a Markdown file"""

        if not self._confirm_save_changes():
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )

        if not file_name:
            return

        file_path = Path(file_name)

        try:
            content = self.file_manager.read_file(file_path)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Open Error", str(error))
            return

        self.current_file_path = file_path
        self.editor.setPlainText(content)
        self.editor.document().setModified(False)
        self.statusBar().showMessage("File opened successfully", self.MESSAGE_TIMEOUT)

    def _save_file(self) -> bool:
        """Save the current document"""

        if self.current_file_path is None:
            return self._save_file_as()

        return self._write_file(self.current_file_path)

    def _save_file_as(self) -> bool:
        """Save the document to a selected location"""

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File",
            "FileNameHere",
            "Markdown Files (*.md);;All files (*)",
        )

        if not file_name:
            return False

        file_path = Path(file_name)

        if not file_path.suffix:
            file_path = file_path.with_suffix(".md")

        if self._write_file(file_path):
            self.current_file_path = file_path
            self.editor.document().setModified(False)
            self._update_window_title()
            return True

        return False

    def _write_file(self, file_path: Path) -> bool:
        """Write the editor content to a file"""

        content = self.editor.toPlainText()

        try:
            self.file_manager.save_file(file_path, content)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Save error", str(error))
            return False

        self.editor.document().setModified(False)
        self.statusBar().showMessage("File saved successfully", self.MESSAGE_TIMEOUT)
        return True

    def closeEvent(self, event):
        """Prevent closing the application with unsaved changes"""

        if self._confirm_save_changes():
            event.accept()
        else:
            event.ignore()
