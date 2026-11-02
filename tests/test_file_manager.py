
import pytest

from markdown_editor.file_manager import FileManager


def test_save_and_read_file(tmp_path):
    """Verify that a file can be saved and read."""
    file_path = tmp_path / "document.md"
    content = "# Markdown Editor\n\nTest content."

    FileManager.save_file(file_path, content)

    result = FileManager.read_file(file_path)

    assert result == content


def test_save_file_with_utf8_characters(tmp_path):
    """Verify that UTF-8 characters are preserved."""
    file_path = tmp_path / "document.md"
    content = "# Introdução\n\nConteúdo em português."

    FileManager.save_file(file_path, content)

    result = FileManager.read_file(file_path)

    assert result == content


def test_read_nonexistent_file(tmp_path):
    """Verify that reading a nonexistent file raises an error."""
    file_path = tmp_path / "nonexistent.md"

    with pytest.raises(FileNotFoundError):
        FileManager.read_file(file_path)


def test_overwrite_existing_file(tmp_path):
    """Verify that saving a file replaces its previous content."""
    file_path = tmp_path / "document.md"

    FileManager.save_file(file_path, "Original content.")
    FileManager.save_file(file_path, "Updated content.")

    assert FileManager.read_file(file_path) == "Updated content."
