import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFontDatabase

from markdown_editor.typography import (
    APPLICATION_FONT_FAMILY,
    APPLICATION_FONT_SIZE,
    EDITOR_DEFAULT_FONT_SIZE,
    EDITOR_FONT_FAMILY,
    PREVIEW_FONT_FAMILY,
    PREVIEW_FONT_SIZE,
    create_application_font,
    create_editor_font,
    create_preview_font,
    load_bundled_fonts,
)


def test_bundled_fonts_are_loaded(qtbot):
    """Register the bundled font families with Qt."""
    loaded_families = load_bundled_fonts()

    assert loaded_families[APPLICATION_FONT_FAMILY] == APPLICATION_FONT_FAMILY
    assert loaded_families[PREVIEW_FONT_FAMILY] == PREVIEW_FONT_FAMILY


def test_application_font_uses_jetbrains_mono(qtbot):
    """Create the application font with the bundled JetBrains Mono family."""
    font = create_application_font()

    assert font.family() == APPLICATION_FONT_FAMILY
    assert font.pointSize() == APPLICATION_FONT_SIZE


def test_editor_font_uses_jetbrains_mono(qtbot):
    """Create the editor font with the bundled JetBrains Mono family."""
    font = create_editor_font()

    assert font.family() == EDITOR_FONT_FAMILY
    assert font.pointSize() == EDITOR_DEFAULT_FONT_SIZE


def test_preview_font_uses_inter(qtbot):
    """Create the preview font with the bundled Inter family."""
    font = create_preview_font()

    assert font.family() == PREVIEW_FONT_FAMILY
    assert font.pointSize() == PREVIEW_FONT_SIZE


def test_font_families_are_registered_with_qt(qtbot):
    """Verify Qt can resolve both bundled font families."""
    load_bundled_fonts()

    available_families = QFontDatabase.families()

    assert APPLICATION_FONT_FAMILY in available_families
    assert PREVIEW_FONT_FAMILY in available_families


def test_font_manager_imports_and_persists_font_files(qtbot, tmp_path):
    """Copy imported fonts into persistent storage and remember their filenames."""
    from markdown_editor.font_manager import FontManager
    from markdown_editor.settings_manager import SettingsManager

    settings = SettingsManager(
        QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )
    from importlib.resources import files

    source_path = files("markdown_editor").joinpath(
        "fonts",
        "JetBrainsMono-Regular.otf",
    )
    manager = FontManager(settings, tmp_path / "fonts")

    family = manager.import_font(source_path)

    assert family == APPLICATION_FONT_FAMILY
    assert len(list((tmp_path / "fonts").glob("*.otf"))) == 1
    assert settings.get(FontManager.IMPORTED_FONTS_KEY, [], list)


def test_font_manager_rejects_unsupported_extensions(qtbot, tmp_path):
    """Reject files whose extensions are not supported font formats."""
    from markdown_editor.font_manager import FontManager
    from markdown_editor.settings_manager import SettingsManager

    settings = SettingsManager(
        QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    )
    source_path = tmp_path / "invalid.txt"
    source_path.write_text("not a font", encoding="utf-8")
    manager = FontManager(settings, tmp_path / "fonts")

    with pytest.raises(ValueError, match="Unsupported font format"):
        manager.import_font(source_path)
