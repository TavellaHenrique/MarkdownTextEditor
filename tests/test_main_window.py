import pytest
from PySide6.QtWidgets import QMessageBox

from markdown_editor.main_window import MainWindow


@pytest.fixture
def main_window(qtbot, monkeypatch):
    """Provide a MainWindow instance without interactive dialogs."""
    # Simulate discarding changes when the test closes the window.
    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Discard,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    yield window

    # Clear the modified state before widget cleanup.
    window.editor.document().setModified(False)


def test_window_initialization(main_window):
    """Verify that the main window initializes correctly."""
    assert main_window.editor is not None
    assert main_window.preview is not None
    assert main_window.current_file_path is None


def test_preview_updates_when_editor_text_changes(main_window):
    """Verify that the preview renders the editor content."""
    main_window.editor.setPlainText("# Preview Test")

    preview_html = main_window.preview.toHtml()

    assert "<h1" in preview_html
    assert "Preview Test" in main_window.preview.toPlainText()


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
    assert main_window.current_file_path == expected_path
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
    assert main_window.current_file_path == file_path
    assert main_window.editor.document().isModified() is False


def test_confirm_save_changes_discards_modifications(main_window, monkeypatch):
    """Verify that choosing Discard allows the operation to continue."""
    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Discard,
    )

    result = main_window._confirm_save_changes()

    assert result is True


def test_confirm_save_changes_cancel(main_window, monkeypatch):
    """Verify that choosing Cancel prevents the operation."""
    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.warning",
        lambda *args: QMessageBox.StandardButton.Cancel,
    )

    result = main_window._confirm_save_changes()

    assert result is False


def test_open_file_handles_read_error(main_window, tmp_path, monkeypatch):
    """Verify that read errors are handled without losing current content."""
    existing_path = tmp_path / "existing.md"
    selected_path = tmp_path / "restricted.md"

    main_window.current_file_path = existing_path
    main_window.editor.setPlainText("Existing content")
    main_window.editor.document().setModified(False)

    monkeypatch.setattr(
        "markdown_editor.main_window.QFileDialog.getOpenFileName",
        lambda *args: (str(selected_path), ""),
    )

    def raise_permission_error(file_path):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        main_window.file_manager,
        "read_file",
        raise_permission_error,
    )

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.critical",
        lambda *args: None,
    )

    main_window._open_file()

    assert main_window.editor.toPlainText() == "Existing content"
    assert main_window.current_file_path == existing_path


def test_save_file_handles_write_error(main_window, tmp_path, monkeypatch):
    """Verify that write errors preserve the modified document state."""
    file_path = tmp_path / "restricted.md"

    main_window.current_file_path = file_path
    main_window.editor.setPlainText("Modified content")
    main_window.editor.document().setModified(True)

    def raise_permission_error(file_path, content):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        main_window.file_manager,
        "save_file",
        raise_permission_error,
    )

    monkeypatch.setattr(
        "markdown_editor.main_window.QMessageBox.critical",
        lambda *args: None,
    )

    result = main_window._save_file()

    assert result is False
    assert main_window.editor.document().isModified() is True
    assert not file_path.exists()