from pathlib import Path

class FileManager:
    """Handle Markdown file operations"""

    @staticmethod
    def read_file(file_path: Path) -> str:
        """Read a text file using UTF-8 encoding"""

        return file_path.read_text(encoding="utf-8")

    @staticmethod
    def save_file(file_path: Path, content: str) -> None:
        """Save the text content using UTF-8 encoding"""

        file_path.write_text(content, encoding="utf-8")