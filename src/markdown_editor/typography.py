from PySide6.QtGui import QFont, QFontDatabase

# Application typography.
APPLICATION_FONT_SIZE = 10

# Editor typography.
EDITOR_DEFAULT_FONT_SIZE = 11
EDITOR_MIN_FONT_SIZE = 8
EDITOR_MAX_FONT_SIZE = 32
EDITOR_FONT_SIZE_STEP = 1

# Markdown preview typography.
PREVIEW_FONT_FAMILY = "Arial, sans-serif"
PREVIEW_FONT_SIZE = 15


def create_application_font() -> QFont:
    """Create the default application font."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(APPLICATION_FONT_SIZE)

    return font


def create_editor_font() -> QFont:
    """Create the default monospaced editor font."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    font.setPointSize(EDITOR_DEFAULT_FONT_SIZE)

    return font
