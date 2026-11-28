from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QComboBox

from markdown_editor.font_manager import FontManager
from markdown_editor.settings_dialog import SettingsDialog
from markdown_editor.settings_manager import SettingsManager
from markdown_editor.typography import (
    APPLICATION_FONT_FAMILY,
    EDITOR_FONT_FAMILY,
    PREVIEW_FONT_FAMILY,
)


def _create_settings_manager(tmp_path):
    """Create isolated settings for a test case."""
    return SettingsManager(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))


def test_typography_page_exposes_font_selectors(qtbot, tmp_path):
    """Display independent selectors for application, editor, and preview fonts."""
    settings = _create_settings_manager(tmp_path)
    manager = FontManager(settings, tmp_path / "fonts")
    dialog = SettingsDialog(settings, font_manager=manager)
    qtbot.addWidget(dialog)

    assert isinstance(dialog.font_combos["application"], QComboBox)
    assert isinstance(dialog.font_combos["editor"], QComboBox)
    assert isinstance(dialog.font_combos["preview"], QComboBox)
    assert dialog.font_combos["application"].currentText() == APPLICATION_FONT_FAMILY
    assert dialog.font_combos["editor"].currentText() == EDITOR_FONT_FAMILY
    assert dialog.font_combos["preview"].currentText() == PREVIEW_FONT_FAMILY


def test_typography_selection_is_persisted(qtbot, tmp_path):
    """Persist a changed font family in the settings manager."""
    settings = _create_settings_manager(tmp_path)
    manager = FontManager(settings, tmp_path / "fonts")
    dialog = SettingsDialog(settings, font_manager=manager)
    qtbot.addWidget(dialog)

    dialog.font_combos["editor"].setCurrentText("Inter")

    assert settings.get("typography/editor_font", value_type=str) == "Inter"


def test_restore_default_fonts_resets_all_selectors(qtbot, tmp_path):
    """Restore the bundled font families and persist their selections."""
    settings = _create_settings_manager(tmp_path)
    settings.set("typography/application_font", "Inter")
    settings.set("typography/editor_font", "Inter")
    settings.set("typography/preview_font", "JetBrains Mono")
    manager = FontManager(settings, tmp_path / "fonts")
    dialog = SettingsDialog(settings, font_manager=manager)
    qtbot.addWidget(dialog)

    dialog._restore_default_fonts()

    assert dialog.font_combos["application"].currentText() == APPLICATION_FONT_FAMILY
    assert dialog.font_combos["editor"].currentText() == EDITOR_FONT_FAMILY
    assert dialog.font_combos["preview"].currentText() == PREVIEW_FONT_FAMILY


def test_theme_selection_emits_theme_changed_signal(qtbot, tmp_path):
    """Emit the internal theme name when the selected theme changes."""
    settings = _create_settings_manager(tmp_path)
    manager = FontManager(settings, tmp_path / "fonts")

    dialog = SettingsDialog(
        settings,
        font_manager=manager,
        theme_names=("dark", "light"),
        current_theme="dark",
    )
    qtbot.addWidget(dialog)

    with qtbot.waitSignal(dialog.theme_changed, timeout=1000) as signal:
        dialog.theme_combo.setCurrentIndex(1)

    assert signal.args == ["light"]
