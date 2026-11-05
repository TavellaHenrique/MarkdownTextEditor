from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from markdown_editor.code_editor import CodeEditor
from markdown_editor.document_controller import DocumentController
from markdown_editor.document_statistics import calculate_document_statistics
from markdown_editor.find_bar import FindBar
from markdown_editor.menu_controller import MenuController
from markdown_editor.preview_controller import PreviewController
from markdown_editor.search_controller import SearchController
from markdown_editor.theme_controller import ThemeController
from markdown_editor.themes import (
    load_application_stylesheet,
)
from markdown_editor.window_controller import WindowController


class MainWindow(QMainWindow):
    """Main application window"""

    INITIAL_WIDTH = 1000
    INITIAL_HEIGHT = 500
    MESSAGE_TIMEOUT = 5000  # ms

    def __init__(self):
        super().__init__()

        # Initialize document management.
        self.document_controller = DocumentController()

        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        self.theme_controller = ThemeController(initial_theme="dark")

        self._create_editor()
        self._create_window_controller()
        self._create_find_bar()
        self._create_preview()
        self._create_splitter()
        self._create_menu_controller()
        self._create_status_bar()
        self._create_search_controller()
        self.window_controller.update_window_title()
        self._apply_theme()

    def _create_editor(self):
        """Create the Markdown text editor"""

        self.editor = CodeEditor()
        self.editor.setPlaceholderText("Out of words?")

        # Send a signal when changes on the text are detected
        self.editor.textChanged.connect(self._update_preview)

    def _create_window_controller(self):
        """Initialize the window controller."""
        self.window_controller = WindowController(
            document=self.editor.document(),
            dialog_parent=self,
            get_file_path=lambda: self.document_controller.current_file_path,
            save_callback=self._save_file,
            set_window_title=self.setWindowTitle,
        )

    def _create_find_bar(self):
        """Create and configure the floating search bar."""
        self.find_bar = FindBar(self.editor)

        self.editor.installEventFilter(self)

    def _create_search_controller(self):
        """Initialize the search controller."""
        self.search_controller = SearchController(
            editor=self.editor,
            find_bar=self.find_bar,
            status_bar=self.statusBar(),
        )

    def _create_preview(self):
        """Create the HTML preview."""
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        self.preview_controller = PreviewController(
            self.preview,
            self.theme_controller,
        )

    def _create_splitter(self):
        """Arrange the editor and preview horizontally"""

        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([self.width() / 2, self.width() / 2])

        self.setCentralWidget(splitter)

    def _create_menu_controller(self):
        """Initialize the menu controller."""
        file_actions = [
            ("Open", "Ctrl+O", self._open_file),
            ("Save", "Ctrl+S", self._save_file),
            ("Save As", "Ctrl+Shift+S", self._save_file_as),
        ]

        edit_actions = [
            ("Undo", "Ctrl+Z", self.editor.undo),
            ("Redo", "Ctrl+Y", self.editor.redo),
            ("Cut", "Ctrl+X", self.editor.cut),
            ("Copy", "Ctrl+C", self.editor.copy),
            ("Paste", "Ctrl+V", self.editor.paste),
            ("Select All", "Ctrl+A", self.editor.selectAll),
            ("Find", "Ctrl+F", self._show_find_bar),
        ]

        view_actions = [
            ("Increase Font Size", "Ctrl+=", self.editor.increase_font_size),
            ("Decrease Font Size", "Ctrl+-", self.editor.decrease_font_size),
            ("Reset Font Size", "Ctrl+0", self.editor.reset_font_size),
        ]

        self.menu_controller = MenuController(
            menu_bar=self.menuBar(),
            parent=self,
            file_actions=file_actions,
            edit_actions=edit_actions,
            view_actions=view_actions,
            theme_names=self.theme_controller.available_themes,
            current_theme=self.theme_controller.current_theme_name,
            on_theme_changed=self._change_theme,
            on_preview_toggled=self.preview.setVisible,
        )

    def _create_status_bar(self):
        """Create and configure the application status bar."""
        status_bar = self.statusBar()

        # Create a container for vertically arranged information.
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 2, 8, 2)
        status_layout.setSpacing(2)

        self.statistics_label = QLabel()
        self.cursor_position_label = QLabel()

        status_layout.addWidget(self.cursor_position_label)
        status_layout.addWidget(self.statistics_label)

        status_bar.addPermanentWidget(status_widget)

        # Connect editor signals to status updates.
        self.editor.textChanged.connect(self._update_document_statistics)
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)

        # Restore the default message when temporary messages disappear.
        status_bar.messageChanged.connect(self._restore_ready_message)

        self._update_cursor_position()
        self._update_document_statistics()
        status_bar.showMessage("Ready")

    def _update_document_statistics(self):
        """Display statistics for the current document."""
        statistics = calculate_document_statistics(self.editor.toPlainText())

        self.statistics_label.setText(
            f"Words: {statistics.word_count} | "
            f"Characters: {statistics.character_count} | "
            f"No whitespace: {statistics.character_count_without_whitespace} | "
            f"Lines: {statistics.line_count} | "
            f"Paragraphs: {statistics.paragraph_count} | "
            f"Reading: {statistics.reading_time_minutes} min"
        )

    def _update_cursor_position(self):
        """Display the current cursor position."""
        cursor = self.editor.textCursor()

        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock() + 1

        self.cursor_position_label.setText(f"Line: {line} | Column: {column}")

    def _apply_theme(self):
        """Apply the currently selected application theme."""
        theme = self.theme_controller.current_theme

        self.setStyleSheet(load_application_stylesheet(theme))

        # Apply theme colors to status information.
        status_text_color = theme.muted_foreground

        self.statistics_label.setStyleSheet(f"color: {status_text_color};")

        self.cursor_position_label.setStyleSheet(f"color: {status_text_color};")

        self.editor.set_line_number_colors(
            theme.gutter_background,
            theme.gutter_foreground,
        )
        self.editor.set_current_line_color(
            theme.current_line_background,
        )
        self.editor.set_search_colors(
            theme.search_highlight,
            theme.current_match,
        )

        # Apply theme colors to find bar information.
        self.find_bar.set_theme_colors(
            foreground=theme.foreground,
            background=theme.menu_background,
        )

        self._update_preview()

    def _change_theme(self, theme_name: str):
        """Change the selected theme and refresh the application."""
        self.theme_controller.set_theme(theme_name)

        self.menu_controller.theme_actions[theme_name].setChecked(True)

        self._apply_theme()

    def _update_preview(self):
        """Update the preview using the current Markdown text."""
        self.preview_controller.update_preview(self.editor.toPlainText())

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
                self.search_controller.update_search(
                    preferred_selection=preferred_selection
                )

            self.find_bar.search_input.setFocus()

        else:
            self.find_bar.show_bar(selected_text)
            self.search_controller.update_search(
                preferred_selection=preferred_selection
            )

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

    def eventFilter(self, watched, event):
        """Keep the search bar positioned when the editor is resized."""

        if (
            watched is self.editor
            and event.type() == QEvent.Type.Resize
            and self.find_bar.isVisible()
        ):
            self._position_find_bar()

        return super().eventFilter(watched, event)

    def _restore_ready_message(self, message: str):
        """Restore the default status message after temporary messages."""
        if not message:
            self.statusBar().showMessage("Ready")

    def _open_file(self):
        """Open a Markdown file."""
        if not self.window_controller.confirm_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )

        if not file_path:
            return

        try:
            content = self.document_controller.load_document(Path(file_path))
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(
                self,
                "Open Error",
                f"Could not open file:\n{error}",
            )
            return

        self.editor.setPlainText(content)
        self.editor.document().setModified(False)

        self.window_controller.update_window_title()
        self.statusBar().showMessage(
            f"Opened: {file_path}",
            3000,
        )

    def _save_file(self) -> bool:
        """Save the current document."""
        file_path = self.document_controller.current_file_path

        if file_path is None:
            return self._save_file_as()

        return self._write_file(file_path)

    def _save_file_as(self) -> bool:
        """Save the document to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )

        if not file_path:
            return False

        path = Path(file_path)

        if not path.suffix:
            path = path.with_suffix(".md")

        return self._write_file(path)

    def _write_file(self, file_path: Path) -> bool:
        """Write the current document to the specified path."""
        content = self.editor.toPlainText()

        try:
            self.document_controller.save_document(
                file_path,
                content,
            )
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save file:\n{error}",
            )
            return False

        self.editor.document().setModified(False)

        self.window_controller.update_window_title()
        self.statusBar().showMessage(
            f"Saved: {file_path}",
            self.MESSAGE_TIMEOUT,
        )

        return True

    def closeEvent(self, event):
        """Prevent closing the application with unsaved changes."""
        if self.window_controller.can_close():
            event.accept()
        else:
            event.ignore()
