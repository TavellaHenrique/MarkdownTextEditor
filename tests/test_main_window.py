import pytest
from PySide6.QtCore import QSettings, QUrl
from PySide6.QtWidgets import QMessageBox

from markdown_editor.document_controller import DocumentController
from markdown_editor.file_manager import FileManager
from markdown_editor.main_window import MainWindow
from markdown_editor.settings_manager import SettingsManager


@pytest.fixture
def main_window(qtbot, monkeypatch, settings_manager):
    """Provide a MainWindow instance without interactive dialogs."""
    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Discard,
    )

    window = MainWindow(settings_manager=settings_manager)
    qtbot.addWidget(window)

    yield window

    # Clear the modified state before widget cleanup.
    window.editor.document().setModified(False)


@pytest.fixture
def settings_manager(tmp_path):
    """Provide an isolated settings manager for each test."""
    settings_file = tmp_path / "settings.ini"

    settings = QSettings(
        str(settings_file),
        QSettings.Format.IniFormat,
    )

    return SettingsManager(settings)


def test_window_initialization(main_window):
    """Verify that the main window initializes correctly."""
    assert main_window.editor is not None
    assert main_window.preview is not None
    assert main_window.document_controller.current_file_path is None


def test_autosave_settings_restore_enabled_state(qtbot, settings_manager):
    """Verify that autosave settings are restored from persistent storage."""
    settings_manager.set("autosave/enabled", False)
    settings_manager.set("autosave/interval", 30_000)

    window = MainWindow(settings_manager=settings_manager)
    qtbot.addWidget(window)

    assert window.auto_save_controller.is_enabled is False
    assert window.auto_save_controller.interval == 30_000


def test_autosave_runs_for_modified_document(main_window, tmp_path):
    """Verify that the autosave controller saves modified documents with a path."""
    file_path = tmp_path / "document.md"
    main_window.document_controller.save_document(file_path, "# Original")
    main_window.editor.setPlainText("# Updated content")
    main_window.editor.document().setModified(True)

    result = main_window.auto_save_controller.save_if_needed()

    assert result is True
    assert file_path.read_text(encoding="utf-8") == "# Updated content"
    assert main_window.editor.document().isModified() is False


def test_preview_updates_when_editor_text_changes(main_window):
    """Verify that the preview renders the editor content."""
    main_window.editor.setPlainText("# Preview Test")

    preview_html = main_window.preview.toHtml()

    assert "<h1" in preview_html
    assert "Preview Test" in main_window.preview.toPlainText()


def test_preview_clicks_open_links_without_reloading_document(main_window, monkeypatch):
    """Verify that preview links are opened externally instead of reloading the QTextBrowser."""
    opened_urls = []

    monkeypatch.setattr(
        "markdown_editor.main_window.QDesktopServices.openUrl",
        lambda url: opened_urls.append(url),
    )

    main_window.preview.anchorClicked.emit(QUrl("https://example.com"))

    assert opened_urls == [QUrl("https://example.com")]


def test_tooltip_style_follows_active_theme(main_window):
    """Ensure the tooltip uses colors from the active theme."""
    main_window.theme_controller.set_theme("dark")
    tooltip_style = main_window._tooltip_style_for_theme(main_window.theme_controller.current_theme)

    assert "QToolTip" in tooltip_style
    assert "color: #e8eaed" in tooltip_style
    assert "background-color: #202124" in tooltip_style
    assert "border: 1px solid #44464a" in tooltip_style


def test_save_file_as_adds_markdown_extension(main_window, tmp_path, monkeypatch):
    """Verify that saving without an extension adds the .md suffix."""
    file_path = tmp_path / "document"

    main_window.editor.setPlainText("# Saved Document")

    monkeypatch.setattr(
        "markdown_editor.main_window.QFileDialog.getSaveFileName",
        lambda *args: (str(file_path), ""),
    )

    result = main_window._save_file_as()

    expected_path = file_path.with_suffix(".md")

    assert result is True
    assert expected_path.exists()
    assert expected_path.read_text(encoding="utf-8") == "# Saved Document"
    assert main_window.document_controller.current_file_path == expected_path
    assert main_window.editor.document().isModified() is False


def test_open_file_loads_content(main_window, tmp_path, monkeypatch):
    """Verify that opening a file loads its content into the editor."""
    file_path = tmp_path / "document.md"
    expected_content = "# Opened Document"

    file_path.write_text(expected_content, encoding="utf-8")

    monkeypatch.setattr(
        "markdown_editor.main_window.QFileDialog.getOpenFileName",
        lambda *args: (str(file_path), ""),
    )

    main_window._open_file()

    assert main_window.editor.toPlainText() == expected_content
    assert main_window.document_controller.current_file_path == file_path
    assert main_window.editor.document().isModified() is False


def test_confirm_save_changes_discards_modifications(main_window, monkeypatch):
    """Verify that choosing Discard allows the operation to continue."""
    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Discard,
    )

    result = main_window.window_controller.confirm_save_changes()

    assert result is True


def test_confirm_save_changes_cancel(main_window, monkeypatch):
    """Verify that choosing Cancel prevents the operation."""
    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Cancel,
    )

    result = main_window.window_controller.confirm_save_changes()

    assert result is False


def test_open_file_handles_read_error(main_window, tmp_path, monkeypatch):
    """Verify that read errors are handled without losing current content."""
    existing_path = tmp_path / "existing.md"
    selected_path = tmp_path / "restricted.md"

    main_window.document_controller.save_document(
        existing_path,
        "Existing content",
    )
    main_window.editor.setPlainText("Existing content")
    main_window.editor.document().setModified(False)

    monkeypatch.setattr(
        "markdown_editor.main_window.QFileDialog.getOpenFileName",
        lambda *args: (str(selected_path), ""),
    )

    def raise_permission_error(file_path):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        main_window.document_controller._file_manager,
        "read_file",
        raise_permission_error,
    )

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.critical",
        lambda *args: None,
    )

    main_window._open_file()

    assert main_window.editor.toPlainText() == "Existing content"
    assert main_window.document_controller.current_file_path == existing_path


def test_save_file_handles_write_error(main_window, tmp_path, monkeypatch):
    """Verify that write errors preserve the modified document state."""
    file_path = tmp_path / "restricted.md"

    file_manager = FileManager()
    controller = DocumentController(
        file_manager=file_manager,
        initial_file_path=file_path,
    )

    main_window.document_controller = controller

    def raise_permission_error(file_path, content):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        file_manager,
        "save_file",
        raise_permission_error,
    )

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.critical",
        lambda *args: None,
    )

    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    result = main_window._save_file()

    assert result is False
    assert main_window.editor.document().isModified()
    assert not file_path.exists()


def test_find_action_exists(main_window):
    """Verify that the Find action exists with the correct shortcut."""

    edit_menu = next(
        action.menu() for action in main_window.menuBar().actions() if action.text() == "Edit"
    )

    find_action = next(action for action in edit_menu.actions() if action.text() == "Find")

    assert find_action.shortcut().toString() == "Ctrl+F"


def test_show_find_bar(main_window, qtbot):
    """Verify that the search bar opens over the editor."""

    main_window.show()
    qtbot.waitExposed(main_window)

    main_window.editor.setPlainText("Markdown Text Editor")

    cursor = main_window.editor.textCursor()
    cursor.select(cursor.SelectionType.WordUnderCursor)
    main_window.editor.setTextCursor(cursor)

    main_window._show_find_bar()

    assert main_window.find_bar.isVisible()
    assert main_window.find_bar.search_input.text() == "Markdown"
    assert main_window.find_bar.parentWidget() is main_window.editor


def test_find_bar_close_restores_editor_focus(main_window, qtbot):
    """Verify that closing the search bar restores editor focus."""
    main_window.show()
    main_window.activateWindow()

    qtbot.waitExposed(main_window)
    qtbot.waitActive(main_window)

    main_window._show_find_bar()
    main_window.find_bar.close_bar()

    assert not main_window.find_bar.isVisible()

    # Wait until the editor receives focus.
    qtbot.waitUntil(main_window.editor.hasFocus)


def test_document_outline_is_visible_by_default(main_window):
    """Verify that the document outline is visible by default."""
    assert not main_window.outline.isHidden()


def test_document_outline_visibility_restores_true(qtbot, settings_manager):
    """Verify that a saved visible state is restored."""
    settings_manager.set("outline/visible", True)

    window = MainWindow(settings_manager=settings_manager)
    qtbot.addWidget(window)

    assert not window.outline.isHidden()


def test_document_outline_visibility_restores_false(qtbot, settings_manager):
    """Verify that a saved hidden state is restored."""
    settings_manager.set("outline/visible", False)

    window = MainWindow(settings_manager=settings_manager)
    qtbot.addWidget(window)

    assert window.outline.isHidden()


def test_document_outline_updates_when_text_changes(main_window):
    """Verify that the outline reflects document headings."""
    main_window.editor.setPlainText("# Main heading\nSome text\n## Secondary heading")

    assert main_window.outline.topLevelItemCount() == 1

    main_item = main_window.outline.topLevelItem(0)

    assert main_item.text(0) == "Main heading"
    assert main_item.childCount() == 1
    assert main_item.child(0).text(0) == "Secondary heading"


def test_document_outline_navigates_to_heading(main_window):
    """Verify that selecting a heading moves the editor cursor."""
    main_window.editor.setPlainText("# First heading\nSome text\n## Second heading")

    main_window._navigate_to_heading(3)

    cursor = main_window.editor.textCursor()

    assert cursor.blockNumber() == 2
    assert cursor.positionInBlock() == 0


def test_document_outline_can_be_hidden(main_window):
    """Verify that the document outline can be hidden."""
    main_window.outline.setVisible(False)

    assert not main_window.outline.isVisible()
