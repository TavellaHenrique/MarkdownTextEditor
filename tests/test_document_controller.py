import pytest

from markdown_editor.document_controller import DocumentController
from markdown_editor.file_manager import FileManager


@pytest.fixture
def controller():
    """Create a document controller instance."""
    return DocumentController()


def test_load_document(controller, tmp_path):
    """Load a document and update the current path."""
    file_path = tmp_path / "document.md"
    expected_content = "# Test document"

    file_path.write_text(expected_content, encoding="utf-8")

    content = controller.load_document(file_path)

    assert content == expected_content
    assert controller.current_file_path == file_path


def test_save_document(controller, tmp_path):
    """Save a document and update the current path."""
    file_path = tmp_path / "document.md"
    content = "# Saved document"

    controller.save_document(file_path, content)

    assert file_path.read_text(encoding="utf-8") == content
    assert controller.current_file_path == file_path


def test_load_document_preserves_path_on_failure(controller, tmp_path):
    """Preserve the current path when loading fails."""
    original_path = tmp_path / "original.md"
    controller.save_document(original_path, "Original content")

    missing_path = tmp_path / "missing.md"

    with pytest.raises((OSError, UnicodeError)):
        controller.load_document(missing_path)

    assert controller.current_file_path == original_path


def test_initial_file_path(tmp_path):
    """Initialize the controller with an existing document path."""
    file_path = tmp_path / "document.md"

    controller = DocumentController(initial_file_path=file_path)

    assert controller.current_file_path == file_path


def test_custom_file_manager(tmp_path):
    """Use the injected file manager for document operations."""
    file_path = tmp_path / "document.md"
    content = "# Custom file manager"

    file_manager = FileManager()
    controller = DocumentController(file_manager=file_manager)

    controller.save_document(file_path, content)

    assert file_path.read_text(encoding="utf-8") == content
    assert controller.current_file_path == file_path


def test_save_document_preserves_path_on_failure(controller, tmp_path, monkeypatch):
    """Preserve the current path when saving fails."""
    original_path = tmp_path / "original.md"
    controller.save_document(original_path, "Original content")

    new_path = tmp_path / "restricted.md"

    def raise_permission_error(file_path, content):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        controller.file_manager,
        "save_file",
        raise_permission_error,
    )

    with pytest.raises(PermissionError):
        controller.save_document(new_path, "New content")

    assert controller.current_file_path == original_path


def test_new_document_resets_current_file_path(controller, tmp_path):
    """Reset the current path when creating a new document."""
    file_path = tmp_path / "document.md"
    controller.save_document(file_path, "# Existing document")

    controller.new_document()

    assert controller.current_file_path is None
