from pathlib import Path

from markdown_editor.file_manager import FileManager


class DocumentController:
    """Coordinate document loading, saving, and file path management."""

    def __init__(
        self,
        file_manager: FileManager | None = None,
        initial_file_path: Path | None = None,
    ):
        """Initialize document management dependencies and state."""
        self._file_manager = file_manager or FileManager()
        self._current_file_path = initial_file_path

    @property
    def file_manager(self) -> FileManager:
        """Return the file manager used by the controller."""
        return self._file_manager

    @property
    def current_file_path(self) -> Path | None:
        """Return the current document path."""
        return self._current_file_path

    def load_document(self, file_path: Path) -> str:
        """Load a document and update its current path."""
        content = self._file_manager.read_file(file_path)

        self._current_file_path = file_path

        return content

    def new_document(self) -> None:
        """Reset the current document path for a new document."""
        self._current_file_path = None

    def save_document(self, file_path: Path, content: str) -> None:
        """Save document content and update its current path."""
        self._file_manager.save_file(file_path, content)

        self._current_file_path = file_path
