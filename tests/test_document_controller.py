import pytest

from markdown_editor.document_controller import DocumentController


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
