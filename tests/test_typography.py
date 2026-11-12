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
