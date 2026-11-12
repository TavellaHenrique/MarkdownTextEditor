import sys

from PySide6.QtWidgets import QApplication

from markdown_editor.main_window import MainWindow


def main():
    """Initialize and execute the application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
