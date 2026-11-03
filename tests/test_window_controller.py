from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox, QWidget

from markdown_editor.window_controller import WindowController


@pytest.fixture
def window_controller(qtbot):
    """Create a window controller with its dependencies."""
    from PySide6.QtGui import QTextDocument

    document = QTextDocument()
    parent = QWidget()
    qtbot.addWidget(parent)

    state = {
        "file_path": None,
        "title": "",
        "save_result": True,
        "save_calls": 0,
    }

    def save_document():
        state["save_calls"] += 1
        return state["save_result"]

    controller = WindowController(
        document=document,
        dialog_parent=parent,
        get_file_path=lambda: state["file_path"],
        save_callback=save_document,
        set_window_title=lambda title: state.update(title=title),
    )

    return controller, document, state


def test_update_window_title(window_controller):
    """Update the title for an unnamed document."""
    controller, _, state = window_controller

    controller.update_window_title()

    assert state["title"] == "Untitled - Markdown Text Editor"


def test_update_window_title_with_modified_document(window_controller):
    """Indicate unsaved changes in the window title."""
    controller, document, state = window_controller

    document.setModified(True)

    assert state["title"] == "Untitled * - Markdown Text Editor"


def test_update_window_title_with_file_path(window_controller):
    """Use the current file name in the window title."""
    controller, _, state = window_controller
    state["file_path"] = Path("document.md")

    controller.update_window_title()

    assert state["title"] == "document.md - Markdown Text Editor"


def test_confirm_save_changes_without_modifications(window_controller):
    """Allow closing when the document has no unsaved changes."""
    controller, _, _ = window_controller

    assert controller.confirm_save_changes() is True


def test_confirm_save_changes_saves_document(
    window_controller,
    monkeypatch,
):
    """Save the document when the user confirms."""
    controller, document, state = window_controller
    document.setModified(True)

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: QMessageBox.StandardButton.Save,
    )

    assert controller.confirm_save_changes() is True
    assert state["save_calls"] == 1


def test_confirm_save_changes_discards_document(
    window_controller,
    monkeypatch,
):
    """Allow closing when the user discards changes."""
    controller, document, state = window_controller
    document.setModified(True)

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: QMessageBox.StandardButton.Discard,
    )

    assert controller.confirm_save_changes() is True
    assert state["save_calls"] == 0


def test_confirm_save_changes_cancels_closing(
    window_controller,
    monkeypatch,
):
    """Prevent closing when the user cancels."""
    controller, document, state = window_controller
    document.setModified(True)

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: QMessageBox.StandardButton.Cancel,
    )

    assert controller.can_close() is False
    assert state["save_calls"] == 0


def test_confirm_save_changes_handles_save_failure(
    window_controller,
    monkeypatch,
):
    """Prevent closing when saving fails."""
    controller, document, state = window_controller
    document.setModified(True)
    state["save_result"] = False

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: QMessageBox.StandardButton.Save,
    )

    assert controller.can_close() is False
