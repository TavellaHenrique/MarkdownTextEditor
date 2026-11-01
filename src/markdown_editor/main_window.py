from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QTextBrowser
)

class MainWindow(QMainWindow):
    """Main application window"""

    INITIAL_WIDTH = 1000
    INITIAL_HEIGHT = 500

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Markdown Text Editor")
        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        self._create_editor()
        self._create_preview()
        self._create_splitter()
        self._create_menu_bar()
        self._create_status_bar()

    def _create_editor(self):
        """Create the Markdown text editor"""

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Out of words?")

    def _create_preview(self):
        """Create the HTML preview"""

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

    def _create_splitter(self):
        """Arrange the editor and preview horizontally"""

        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([self.width()/2, self.width()/2])

        self.setCentralWidget(splitter)

    def _create_menu_bar(self):
        """Create the application menu bar"""

        menu_bar = self.menuBar()

        menu_bar.addMenu("File")
        menu_bar.addMenu("Edit")
        menu_bar.addMenu("View")

    def _create_status_bar(self):
        """Create the application status bar"""

        self.statusBar().showMessage("Status: Ready")