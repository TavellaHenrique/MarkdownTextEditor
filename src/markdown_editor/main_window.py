from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTextBrowser
)

from markdown_editor.markdown_parser import MarkdownParser
from markdown_editor.file_manager import FileManager

class MainWindow(QMainWindow):
    """Main application window"""

    INITIAL_WIDTH = 1000
    INITIAL_HEIGHT = 500
    STATUS_BAR_MESSAGE_TIMEOUT = 5000 # ms

    def __init__(self):
        super().__init__()

        # Initialize the File Manager
        self.current_file_path = None
        self.file_manager = FileManager()

        # Initialize the Markdown parser
        self.markdown_parser = MarkdownParser()

        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        self._create_editor()
        self._create_preview()
        self._create_splitter()
        self._create_menu_bar()
        self._create_status_bar()
        self._update_window_title()

    def _create_editor(self):
        """Create the Markdown text editor"""

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Out of words?")

        # Send a signal when changes on the text are detected
        self.editor.textChanged.connect(self._update_preview)

        # Send a signal when document changes
        self.editor.document().modificationChanged.connect(self._update_window_title)

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

        self._create_file_menu()
        menu_bar.addMenu("Edit")
        menu_bar.addMenu("View")

    def _create_file_menu(self):
        file_menu = self.menuBar().addMenu("File")
        actions = []
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        actions.append(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        actions.append(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_file_as)
        actions.append(save_as_action)

        for action in actions:
            file_menu.addAction(action)

    def _create_status_bar(self):
        """Create the application status bar"""

        self.statusBar().showMessage("Ready")

    def _update_preview(self):
            """Update the HTML preview using the current Markdown text"""
        
            mardown_text = self.editor.toPlainText()
            html_content = self.markdown_parser.to_html(mardown_text)
            
            self.preview.setHtml(html_content)

    def _update_window_title(self, modified=False):
            """Update the current window title with the file name and modification state"""
    
            if self.current_file_path:
                file_name = self.current_file_path
            else:
                file_name = "Untitled"
            
            modified_marker = "*" if modified else ""
    
            self.setWindowTitle(f"{modified_marker} {file_name} - Markdown Text Editor")

    def _confirm_save_changes(self) -> bool:
        """Ask whether unsaved changes should be saved or discarded"""

        if not self.editor.document().isModified():
            return True

        answer = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "This document has unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Save:
            return self._save_file()

        return answer == QMessageBox.StandardButton.Discard

    def _open_file(self):
        """Open a Markdown file"""

        if not self._confirm_save_changes():
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )

        if not file_name:
            return

        file_path = Path(file_name)

        try:
            content = self.file_manager.read_file(file_path)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Open Error", str(error))
            return

        self.current_file_path = file_path
        self.editor.setPlainText(content)
        self.editor.document().setModified(False)
        self.statusBar().showMessage("File opened successfully", self.STATUS_BAR_MESSAGE_TIMEOUT)

    def _save_file(self) -> bool:
        """Save the current document"""

        if self.current_file_path is None:
            return self._save_file_as()

        return self._write_file(self.current_file_path)

    def _save_file_as(self) -> bool:
        """Save the document to a selected location"""

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File",
            "FileNameHere",
            "Markdown Files (*.md);;All files (*)",
        )

        if not file_name:
            return False

        file_path = Path(file_name)

        if not file_path.suffix:
            file_path = file_path.with_suffix(".md")

        if self._write_file(file_path):
            self.current_file_path = file_path
            self.editor.document().setModified(False)
            self._update_window_title()
            return True

        return False

    def _write_file(self, file_path: Path) -> bool:
        """Write the editor content to a file"""

        content = self.editor.toPlainText()

        try:
            self.file_manager.save_file(file_path, content)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Save error", str(error))
            return False

        self.editor.document().setModified(False)
        self.statusBar().showMessage("File saved successfully", self.STATUS_BAR_MESSAGE_TIMEOUT)
        return True

    def closeEvent(self, event):
        """Prevent closing the application with unsaved changes"""

        if self._confirm_save_changes():
            event.accept()
        else:
            event.ignore()
