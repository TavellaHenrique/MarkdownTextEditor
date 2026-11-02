import sys

from PySide6.QtWidgets import QApplication

from markdown_editor.main_window import MainWindow
from markdown_editor.typography import create_application_font


def main():
    """Initialize and execute the application."""
    app = QApplication(sys.argv)
    app.setFont(create_application_font())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
