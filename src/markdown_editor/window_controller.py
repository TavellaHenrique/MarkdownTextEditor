from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QMessageBox, QWidget


class WindowController:
    """Coordinate window title updates and closing confirmation."""

    def __init__(
        self,
        document: QTextDocument,
        dialog_parent: QWidget,
        get_file_path: Callable[[], Path | None],
        save_callback: Callable[[], bool],
        set_window_title: Callable[[str], None],
    ):
        """Initialize the controller with explicit dependencies."""
        self._document = document
        self._dialog_parent = dialog_parent
        self._get_file_path = get_file_path
        self._save_callback = save_callback
        self._set_window_title = set_window_title

        self._document.modificationChanged.connect(self.update_window_title)

    def update_window_title(self, _modified: bool | None = None) -> None:
        """Update the window title according to document state."""
        file_path = self._get_file_path()
        file_name = file_path.name if file_path else "Untitled"

        modified = self._document.isModified()
        title = f"{file_name}{' *' if modified else ''} - Markdown Text Editor"

        self._set_window_title(title)

    def confirm_save_changes(self) -> bool:
        """Ask whether unsaved changes should be saved or discarded."""
        if not self._document.isModified():
            return True

        answer = QMessageBox.warning(
            self._dialog_parent,
            "Unsaved Changes",
            "This document has unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Save:
            return self._save_callback()

        return answer == QMessageBox.StandardButton.Discard

    def can_close(self) -> bool:
        """Determine whether the application window can close."""
        return self.confirm_save_changes()
