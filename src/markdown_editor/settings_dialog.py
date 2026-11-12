from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from markdown_editor.font_manager import FontManager
from markdown_editor.settings_manager import SettingsManager
from markdown_editor.typography import (
    APPLICATION_FONT_FAMILY,
    EDITOR_FONT_FAMILY,
    PREVIEW_FONT_FAMILY,
)


class SettingsDialog(QDialog):
    """Display application settings grouped into navigable sections."""

    typography_changed = Signal(str, str, str)

    SECTIONS = (
        ("Appearance", "Configure the application's visual appearance."),
        ("Typography", "Manage application, editor, and preview fonts."),
        ("Editor", "Configure editing behavior and editor preferences."),
        ("Preview", "Configure Markdown preview behavior and presentation."),
        ("Files & Saving", "Configure file handling and automatic saving."),
    )

    FONT_SETTINGS = {
        "application": "typography/application_font",
        "editor": "typography/editor_font",
        "preview": "typography/preview_font",
    }

    DEFAULT_FONTS = {
        "application": APPLICATION_FONT_FAMILY,
        "editor": EDITOR_FONT_FAMILY,
        "preview": PREVIEW_FONT_FAMILY,
    }

    def __init__(
        self,
        settings_manager: SettingsManager,
        parent: QWidget | None = None,
        font_manager: FontManager | None = None,
    ) -> None:
        """Initialize the settings dialog and its navigation."""
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.font_manager = font_manager or FontManager(settings_manager)
        self.font_combos: dict[str, QComboBox] = {}

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
            if title == "Typography":
                page = self._create_typography_page(description)
            else:
                page = self._create_section_page(title, description)
            self.pages.addWidget(page)

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

    def _create_typography_page(self, description: str) -> QWidget:
        """Create controls for selecting and importing font families."""
        page = QWidget(self.pages)
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Typography", page)
        title_label.setObjectName("settings_section_title")

        description_label = QLabel(description, page)
        description_label.setWordWrap(True)

        form_layout = QFormLayout()
        available_families = self.font_manager.available_families()

        for key, label in (
            ("application", "Application font"),
            ("editor", "Editor font"),
            ("preview", "Preview font"),
        ):
            combo = QComboBox(page)
            combo.setObjectName(f"{key}_font_combo")
            combo.addItems(available_families)

            default_family = self.DEFAULT_FONTS[key]
            saved_family = self.settings_manager.get(
                self.FONT_SETTINGS[key],
                default_family,
                str,
            )
            selected_family = saved_family if saved_family in available_families else default_family
            combo.setCurrentText(selected_family)
            combo.currentTextChanged.connect(
                lambda family, setting_key=key: self._save_font_selection(
                    setting_key,
                    family,
                )
            )
            self.font_combos[key] = combo
            form_layout.addRow(label, combo)

        import_button = QPushButton("Import Font", page)
        import_button.setObjectName("import_font_button")
        import_button.clicked.connect(self._import_font)

        restore_button = QPushButton("Restore Defaults", page)
        restore_button.setObjectName("restore_default_fonts_button")
        restore_button.clicked.connect(self._restore_default_fonts)

        button_layout = QHBoxLayout()
        button_layout.addWidget(import_button)
        button_layout.addWidget(restore_button)
        button_layout.addStretch(1)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addSpacing(16)
        layout.addLayout(form_layout)
        layout.addSpacing(12)
        layout.addLayout(button_layout)
        layout.addStretch(1)

        return page

    def _save_font_selection(self, key: str, family: str) -> None:
        """Persist a font selection and notify the main window."""
        self.settings_manager.set(self.FONT_SETTINGS[key], family)
        self.settings_manager.sync()
        self._emit_typography_changed()

    def _emit_typography_changed(self) -> None:
        """Emit the currently selected font families."""
        self.typography_changed.emit(
            self.font_combos["application"].currentText(),
            self.font_combos["editor"].currentText(),
            self.font_combos["preview"].currentText(),
        )

    def _import_font(self) -> None:
        """Import a font file and add its family to each selector."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Font",
            "",
            "Font Files (*.otf *.ttf *.ttc *.otc)",
        )
        if not file_path:
            return

        try:
            family = self.font_manager.import_font(file_path)
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Font Import Failed", str(error))
            return

        for combo in self.font_combos.values():
            if combo.findText(family) < 0:
                combo.addItem(family)

    def _restore_default_fonts(self) -> None:
        """Restore and persist the bundled font families."""
        for key, default_family in self.DEFAULT_FONTS.items():
            combo = self.font_combos[key]
            combo.setCurrentText(default_family)
            self.settings_manager.set(self.FONT_SETTINGS[key], default_family)

        self.settings_manager.sync()
        self._emit_typography_changed()
