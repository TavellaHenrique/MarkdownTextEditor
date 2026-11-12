from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from markdown_editor.settings_manager import SettingsManager


class SettingsDialog(QDialog):
    """Display application settings grouped into navigable sections."""

    SECTIONS = (
        ("Appearance", "Configure the application's visual appearance."),
        ("Typography", "Manage application, editor, and preview fonts."),
        ("Editor", "Configure editing behavior and editor preferences."),
        ("Preview", "Configure Markdown preview behavior and presentation."),
        ("Files & Saving", "Configure file handling and automatic saving."),
    )

    def __init__(
        self,
        settings_manager: SettingsManager,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the settings dialog and its navigation."""
        super().__init__(parent)
        self.settings_manager = settings_manager

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(720, 440)

        self.category_list = QListWidget(self)
        self.category_list.setObjectName("settings_category_list")
        self.category_list.setFixedWidth(180)

        self.pages = QStackedWidget(self)
        self.pages.setObjectName("settings_pages")

        for title, description in self.SECTIONS:
            self.category_list.addItem(title)
            self.pages.addWidget(self._create_section_page(title, description))

        self.category_list.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.category_list.setCurrentRow(0)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.category_list)
        content_layout.addWidget(self.pages, 1)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        button_box.rejected.connect(self.reject)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.addLayout(content_layout)
        dialog_layout.addWidget(button_box)

    def _create_section_page(self, title: str, description: str) -> QWidget:
        """Create a placeholder page for a settings category."""
        page = QWidget(self.pages)
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel(title, page)
        title_label.setObjectName("settings_section_title")

        description_label = QLabel(description, page)
        description_label.setWordWrap(True)

        placeholder_label = QLabel(
            "Settings for this section will be available here.",
            page,
        )
        placeholder_label.setObjectName("settings_section_placeholder")
        placeholder_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addSpacing(16)
        layout.addWidget(placeholder_label)

        return page
