from functools import lru_cache
from importlib.resources import files

from PySide6.QtGui import QFont, QFontDatabase

# Bundled font families.
APPLICATION_FONT_FAMILY = "JetBrains Mono"
EDITOR_FONT_FAMILY = "JetBrains Mono"
PREVIEW_FONT_FAMILY = "Inter"

# Application typography.
APPLICATION_FONT_SIZE = 10

# Editor typography.
EDITOR_DEFAULT_FONT_SIZE = 11
EDITOR_MIN_FONT_SIZE = 8
EDITOR_MAX_FONT_SIZE = 32
EDITOR_FONT_SIZE_STEP = 1

# Markdown preview typography.
PREVIEW_FONT_SIZE = 15


@lru_cache(maxsize=1)
def load_bundled_fonts() -> dict[str, str]:
    """Load bundled font files and return their registered family names."""
    font_directory = files("markdown_editor").joinpath("fonts")
    font_files = {
        APPLICATION_FONT_FAMILY: "JetBrainsMono-Regular.otf",
        PREVIEW_FONT_FAMILY: "Inter-Regular.otf",
    }

    loaded_families = {}

    for expected_family, filename in font_files.items():
        font_path = font_directory.joinpath(filename)
        font_id = QFontDatabase.addApplicationFont(str(font_path))

        if font_id < 0:
            raise RuntimeError(f"Unable to load bundled font: {filename}")

        families = QFontDatabase.applicationFontFamilies(font_id)

        if expected_family not in families:
            raise RuntimeError(
                f"Font file {filename} does not provide the expected family '{expected_family}'."
            )

        loaded_families[expected_family] = expected_family

    return loaded_families


def create_application_font(family: str = APPLICATION_FONT_FAMILY) -> QFont:
    """Create the application font using the selected family."""
    load_bundled_fonts()

    font = QFont(family)
    font.setPointSize(APPLICATION_FONT_SIZE)

    return font


def create_editor_font(family: str = EDITOR_FONT_FAMILY) -> QFont:
    """Create the editor font using the selected family."""
    load_bundled_fonts()

    font = QFont(family)
    font.setPointSize(EDITOR_DEFAULT_FONT_SIZE)

    return font


def create_preview_font(family: str = PREVIEW_FONT_FAMILY) -> QFont:
    """Create the preview font using the selected family."""
    load_bundled_fonts()

    font = QFont(family)
    font.setPointSize(PREVIEW_FONT_SIZE)

    return font
