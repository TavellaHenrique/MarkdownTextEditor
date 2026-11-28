from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, Qt
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from markdown_editor.autosave_controller import AutoSaveController
from markdown_editor.code_editor import CodeEditor
from markdown_editor.document_controller import DocumentController
from markdown_editor.document_outline import DocumentOutline
from markdown_editor.document_statistics import calculate_document_statistics
from markdown_editor.find_bar import FindBar
from markdown_editor.font_manager import FontManager
from markdown_editor.markdown_parser import MarkdownParser
from markdown_editor.menu_controller import MenuController
from markdown_editor.preview_controller import PreviewBrowser, PreviewController
from markdown_editor.search_controller import SearchController
from markdown_editor.settings_dialog import SettingsDialog
from markdown_editor.settings_manager import SettingsManager
from markdown_editor.theme_controller import ThemeController
from markdown_editor.themes import load_application_stylesheet
from markdown_editor.typography import create_application_font
from markdown_editor.window_controller import WindowController


class MainWindow(QMainWindow):
    """Main application window"""

    INITIAL_WIDTH = 1000
    INITIAL_HEIGHT = 500
    MESSAGE_TIMEOUT = 5000  # ms

    def __init__(
        self,
        settings_manager: SettingsManager | None = None,
    ):
        super().__init__()

        self.settings_manager = (
            settings_manager if settings_manager is not None else SettingsManager()
        )
        application = QApplication.instance()
        application.setOrganizationName(SettingsManager.ORGANIZATION_NAME)
        application.setApplicationName(SettingsManager.APPLICATION_NAME)

        self.font_manager = FontManager(self.settings_manager)
        available_fonts = self.font_manager.available_families()
        self._application_font_family = self._get_font_preference(
            "application",
            available_fonts,
        )
        self._editor_font_family = self._get_font_preference("editor", available_fonts)
        self._preview_font_family = self._get_font_preference("preview", available_fonts)

        # Apply the selected application font before creating child widgets.
        QApplication.instance().setFont(create_application_font(self._application_font_family))

        self.document_controller = DocumentController()
        self.markdown_parser = MarkdownParser()

        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        self.theme_controller = ThemeController(initial_theme="dark")

        saved_theme = self.settings_manager.get(
            "appearance/theme",
            value_type=str,
        )

        if saved_theme in self.theme_controller.available_themes:
            self.theme_controller.set_theme(saved_theme)

        self._create_editor()
        self._create_auto_save_controller()
        self._create_window_controller()
        self._create_find_bar()
        self._create_preview()
        self._create_outline()
        self._create_splitter()
        self._restore_window_state()
        self._create_menu_controller()
        self._restore_panel_visibility_settings()
        self._create_status_bar()
        self._create_search_controller()

        self.window_controller.update_window_title()
        self._apply_theme()

    def _create_editor(self):
        """Create the Markdown text editor"""

        self.editor = CodeEditor()
        self.editor.set_font_family(self._editor_font_family)

        self.editor.set_font_size(
            self.settings_manager.get(
                "editor/font_size",
                value_type=int,
            )
        )

        self.editor.setPlaceholderText("Out of words?")

        self.editor_label = QLabel("Editor")
        self.editor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor_label.setContentsMargins(8, 4, 8, 4)

        self.editor_panel = QWidget()
        editor_layout = QVBoxLayout(self.editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.editor_label)
        editor_layout.addWidget(self.editor)

        # Send a signal when changes on the text are detected
        self.editor.textChanged.connect(self._update_preview)

    def _create_auto_save_controller(self):
        """Create the periodic save controller for the editor."""
        interval = self.settings_manager.get(
            "autosave/interval",
            value_type=int,
        )
        enabled = self.settings_manager.get(
            "autosave/enabled",
            value_type=bool,
        )

        self.auto_save_controller = AutoSaveController(
            document=self.editor.document(),
            get_file_path=lambda: self.document_controller.current_file_path,
            save_callback=self._save_file,
            interval=interval,
            enabled=enabled,
        )

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
        self.preview = PreviewBrowser()
        self.preview.setOpenLinks(False)
        self.preview.setOpenExternalLinks(False)
        self.preview.anchorClicked.connect(self._open_link)

        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setContentsMargins(8, 4, 8, 4)

        self.preview_panel = QWidget()
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview)

        self.preview_controller = PreviewController(
            self.preview,
            self.theme_controller,
            font_family=self._preview_font_family,
        )

    def _open_link(self, url):
        """Open clicked preview links via the system browser without reloading the document."""
        if not url.isValid():
            return

        QDesktopServices.openUrl(url)

    def _create_outline(self):
        """Create the document navigation panel."""
        self.outline = DocumentOutline()

        self.outline_label = QLabel("Outline")
        self.outline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.outline_label.setContentsMargins(8, 4, 8, 4)

        self.outline_panel = QWidget()
        outline_layout = QVBoxLayout(self.outline_panel)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(0)
        outline_layout.addWidget(self.outline_label)
        outline_layout.addWidget(self.outline)

        self.outline.heading_selected.connect(self._navigate_to_heading)

        self.editor.textChanged.connect(self._update_document_outline)

        self._update_document_outline()

    def _update_document_outline(self):
        """Refresh the document outline using the current Markdown text."""
        markdown_text = self.editor.toPlainText()
        headings = self.markdown_parser.extract_headings(markdown_text)

        self.outline.set_headings(headings)

    def _navigate_to_heading(self, line_number: int):
        """Move the editor cursor to the selected heading."""
        block = self.editor.document().findBlockByNumber(line_number - 1)

        if not block.isValid():
            return

        cursor = QTextCursor(block)
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()

    def _create_splitter(self):
        """Arrange the outline, editor, and preview panels."""
        self.editor_preview_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_preview_splitter.addWidget(self.editor_panel)
        self.editor_preview_splitter.addWidget(self.preview_panel)
        self.editor_preview_splitter.setSizes([500, 500])

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.outline_panel)
        self.main_splitter.addWidget(self.editor_preview_splitter)
        self.main_splitter.setSizes([200, 800])

        self.setCentralWidget(self.main_splitter)

    def _restore_window_state(self) -> None:
        """Restore the window geometry and splitter positions."""
        geometry = self.settings_manager.get(
            "window/geometry",
            QByteArray(),
            QByteArray,
        )

        if not geometry.isEmpty():
            self.restoreGeometry(geometry)

        main_splitter_state = self.settings_manager.get(
            "window/main_splitter",
            QByteArray(),
            QByteArray,
        )

        if not main_splitter_state.isEmpty():
            self.main_splitter.restoreState(main_splitter_state)

        preview_splitter_state = self.settings_manager.get(
            "window/preview_splitter",
            QByteArray(),
            QByteArray,
        )

        if not preview_splitter_state.isEmpty():
            self.editor_preview_splitter.restoreState(preview_splitter_state)

    def _create_menu_controller(self):
        """Initialize the menu controller."""
        file_actions = [
            ("New", "Ctrl+N", self._new_file),
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

        format_actions = [
            ("Bold", "Ctrl+B", self.editor.format_bold),
            ("Italic", "Ctrl+I", self.editor.format_italic),
            ("Horizontal Rule", "Ctrl+Alt+H", self.editor.insert_horizontal_rule),
            ("Line Break", "Ctrl+Shift+R", self.editor.insert_line_break),
            ("Blockquote", "Ctrl+Alt+Q", self.editor.insert_blockquote),
            ("Link", "Ctrl+K", self.editor.insert_link),
            ("Hidden Comment", "Ctrl+Shift+C", self.editor.insert_hidden_comment),
        ]

        code_actions = [
            ("Inline Code", "Ctrl+Alt+C", self.editor.insert_inline_code),
            ("Fenced Code Block", "Ctrl+Alt+F", self.editor.insert_fenced_code_block),
        ]

        list_actions = [
            ("Ordered List", "Ctrl+Alt+O", self.editor.insert_ordered_list),
            ("Unordered List", "Ctrl+Alt+U", self.editor.insert_unordered_list),
        ]

        heading_actions = [
            (
                f"Heading {level}",
                f"Ctrl+{level}",
                lambda checked=False, level=level: self.editor.set_heading_level(level),
            )
            for level in range(1, 7)
        ]

        self.menu_controller = MenuController(
            menu_bar=self.menuBar(),
            parent=self,
            file_actions=file_actions,
            edit_actions=edit_actions,
            view_actions=view_actions,
            on_preview_toggled=self._toggle_preview_panel,
            on_outline_toggled=self._toggle_outline_panel,
            format_actions=format_actions,
            heading_actions=heading_actions,
            list_actions=list_actions,
            code_actions=code_actions,
            on_settings_requested=self._show_settings_dialog,
        )

    def _show_settings_dialog(self, _checked: bool = False) -> None:
        """Open the application settings dialog."""
        dialog = SettingsDialog(
            self.settings_manager,
            self,
            font_manager=self.font_manager,
            theme_names=self.theme_controller.available_themes,
            current_theme=self.theme_controller.current_theme_name,
        )

        dialog.typography_changed.connect(self._apply_typography)
        dialog.theme_changed.connect(self._change_theme)

        dialog.auto_save_enabled_changed.connect(self._set_auto_save_enabled)
        dialog.auto_save_interval_changed.connect(self._set_auto_save_interval)

        dialog.exec()

    def _get_font_preference(self, key: str, available_fonts: list[str]) -> str:
        """Return a valid saved font family or the corresponding bundled default."""
        defaults = {
            "application": "JetBrains Mono",
            "editor": "JetBrains Mono",
            "preview": "Inter",
        }
        saved_family = self.settings_manager.get(
            f"typography/{key}_font",
            defaults[key],
            str,
        )
        return saved_family if saved_family in available_fonts else defaults[key]

    def _apply_typography(
        self,
        application_family: str,
        editor_family: str,
        preview_family: str,
    ) -> None:
        """Apply font family changes to the application, editor, and preview."""
        self._application_font_family = application_family
        self._editor_font_family = editor_family
        self._preview_font_family = preview_family

        QApplication.instance().setFont(create_application_font(application_family))
        self.editor.set_font_family(editor_family)
        self.preview_controller.set_font_family(preview_family)
        self._update_preview()

    def _toggle_preview_panel(self, visible: bool):
        """Toggle the preview panel and its title together."""
        self.preview_panel.setVisible(visible)
        self.preview_label.setVisible(visible)
        self.preview.setVisible(visible)

    def _toggle_outline_panel(self, visible: bool):
        """Toggle the outline panel and its title together."""
        self.outline_panel.setVisible(visible)
        self.outline_label.setVisible(visible)
        self.outline.setVisible(visible)

    def _restore_panel_visibility_settings(self):
        # Restore panel visibility settings.
        preview_visible = self.settings_manager.get(
            "preview/visible",
            value_type=bool,
        )

        outline_visible = self.settings_manager.get(
            "outline/visible",
            value_type=bool,
        )

        self._toggle_preview_panel(preview_visible)
        self._toggle_outline_panel(outline_visible)
        self.menu_controller.preview_action.setChecked(preview_visible)
        self.menu_controller.outline_action.setChecked(outline_visible)

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

    def _tooltip_style_for_theme(self, theme):
        """Return the tooltip stylesheet for the active theme."""
        return f"""
        QToolTip {{
            color: {theme.foreground};
            background-color: {theme.background};
            border: 1px solid {theme.border};
            border-radius: 6px;
            padding: 2px 4px;
            font-size: 12px;
        }}
        """

    def _apply_theme(self):
        """Apply the currently selected application theme."""
        theme = self.theme_controller.current_theme

        self.setStyleSheet(
            load_application_stylesheet(theme) + self._tooltip_style_for_theme(theme)
        )

        # Apply theme colors to status information.
        status_text_color = theme.muted_foreground
        panel_text_color = theme.foreground

        self.statistics_label.setStyleSheet(f"color: {status_text_color};")
        self.cursor_position_label.setStyleSheet(f"color: {status_text_color};")

        for label in (
            self.outline_label,
            self.editor_label,
            self.preview_label,
        ):
            label.setStyleSheet(
                f"color: {panel_text_color}; background-color: transparent; text-align: center;"
            )

        self.editor.set_line_number_colors(
            theme.gutter_background,
            theme.gutter_foreground,
        )
        self.editor.set_current_line_color(
            theme.current_line_background,
        )
        self.editor.set_placeholder_color(theme.muted_foreground)
        self.editor.set_search_colors(
            theme.search_highlight,
            theme.current_match,
        )

        # Apply theme colors to find bar information.
        self.find_bar.set_theme_colors(
            foreground=theme.foreground,
            background=theme.menu_background,
        )

        # Apply theme colors to the document outline.
        self.outline.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: {theme.menu_background};
                color: {theme.foreground};
                border: 1px solid {theme.border};
            }}

            QTreeWidget::item:selected {{
                background-color: {theme.menu_selected};
                color: {theme.foreground};
            }}

            QTreeWidget::item:hover {{
                background-color: {theme.menu_selected};
            }}
            """
        )

        self._update_preview()

    def _change_theme(self, theme_name: str) -> None:
        """Change the selected theme and refresh the application."""
        self.theme_controller.set_theme(theme_name)
        self.settings_manager.set("appearance/theme", theme_name)
        self.settings_manager.sync()
        self._apply_theme()

    def _set_auto_save_enabled(self, enabled: bool):
        """Enable or disable the automatic save feature."""
        self.auto_save_controller.set_enabled(enabled)
        self.settings_manager.set("autosave/enabled", enabled)
        self.settings_manager.sync()

    def _set_auto_save_interval(self, interval: int):
        """Update the automatic save interval and persist it."""
        self.auto_save_controller.set_interval(interval)
        self.settings_manager.set("autosave/interval", interval)
        self.settings_manager.sync()

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
                self.search_controller.update_search(preferred_selection=preferred_selection)

            self.find_bar.search_input.setFocus()

        else:
            self.find_bar.show_bar(selected_text)
            self.search_controller.update_search(preferred_selection=preferred_selection)

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

    def _save_settings(self) -> None:
        """Persist application preferences and window state."""
        self.settings_manager.set(
            "appearance/theme",
            self.theme_controller.current_theme_name,
        )

        self.settings_manager.set(
            "editor/font_size",
            self.editor.font_size,
        )

        self.settings_manager.set(
            "preview/visible",
            self.menu_controller.preview_action.isChecked(),
        )

        # Save outline visibility.
        self.settings_manager.set(
            "outline/visible",
            self.menu_controller.outline_action.isChecked(),
        )

        self.settings_manager.set(
            "window/geometry",
            self.saveGeometry(),
        )

        self.settings_manager.set(
            "window/main_splitter",
            self.main_splitter.saveState(),
        )

        self.settings_manager.set(
            "window/preview_splitter",
            self.editor_preview_splitter.saveState(),
        )

        self.settings_manager.set(
            "autosave/enabled",
            self.auto_save_controller.is_enabled,
        )

        self.settings_manager.set(
            "autosave/interval",
            self.auto_save_controller.interval,
        )

        self.settings_manager.sync()

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

    def _new_file(self, _checked=False):
        """Create a new empty document after user confirmation."""
        answer = QMessageBox.question(
            self,
            "New Document",
            "Are you sure you want to create a new document?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if not self.window_controller.confirm_save_changes():
            return

        self.document_controller.new_document()
        self.editor.clear()
        self.editor.document().setModified(False)

        self.window_controller.update_window_title()
        self.statusBar().showMessage("New document", self.MESSAGE_TIMEOUT)

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
        """Save settings before closing the application."""
        if self.window_controller.can_close():
            self._save_settings()
            event.accept()
        else:
            event.ignore()


def test_settings_pages_are_added_to_stacked_widget(qtbot, settings_dialog):
    """Ensure every settings category has a corresponding page."""
    qtbot.addWidget(settings_dialog)

    assert settings_dialog.pages.count() == len(settings_dialog.SECTIONS)


def test_selecting_category_changes_visible_page(qtbot, settings_dialog):
    """Display the corresponding page when selecting a category."""
    qtbot.addWidget(settings_dialog)

    settings_dialog.category_list.setCurrentRow(1)

    assert settings_dialog.pages.currentIndex() == 1
