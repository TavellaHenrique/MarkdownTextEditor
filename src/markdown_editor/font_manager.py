import shutil
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QFontDatabase

from markdown_editor.settings_manager import SettingsManager
from markdown_editor.typography import load_bundled_fonts


class FontManager:
    """Register bundled and user-imported fonts for the application."""

    SUPPORTED_EXTENSIONS = {".otf", ".ttf", ".ttc", ".otc"}
    IMPORTED_FONTS_KEY = "typography/imported_fonts"

    def __init__(
        self,
        settings_manager: SettingsManager,
        fonts_directory: Path | None = None,
    ) -> None:
        """Initialize the font manager and restore previously imported fonts."""
        self._settings_manager = settings_manager
        self._fonts_directory = fonts_directory or self._default_fonts_directory()
        self._registered_font_ids: list[int] = []
        self._fonts_directory.mkdir(parents=True, exist_ok=True)
        load_bundled_fonts()
        self.load_imported_fonts()

    @staticmethod
    def _default_fonts_directory() -> Path:
        """Return the persistent application data directory for imported fonts."""
        app_data_path = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        return Path(app_data_path) / "fonts"

    @property
    def fonts_directory(self) -> Path:
        """Expose the font storage directory."""
        return self._fonts_directory

    def available_families(self) -> list[str]:
        """Return all font families currently registered with Qt."""
        return sorted(set(QFontDatabase.families()), key=str.casefold)

    def load_imported_fonts(self) -> None:
        """Register imported font files saved by previous application sessions."""
        filenames = self._settings_manager.get(
            self.IMPORTED_FONTS_KEY,
            [],
            list,
        )

        for filename in filenames:
            if Path(filename).name != filename:
                continue

            font_path = self._fonts_directory / filename
            if not font_path.is_file():
                continue

            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id >= 0:
                self._registered_font_ids.append(font_id)

    def import_font(self, source_path: str | Path) -> str:
        """Copy, validate, and register a font file; return its family name."""
        source = Path(source_path)

        if not source.is_file():
            raise FileNotFoundError(f"Font file does not exist: {source}")

        if source.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported font format. Use OTF, TTF, TTC, or OTC.")

        destination = self._unique_destination(source.name)
        shutil.copy2(source, destination)

        font_id = QFontDatabase.addApplicationFont(str(destination))
        if font_id < 0:
            destination.unlink(missing_ok=True)
            raise ValueError("Qt could not register this font file.")

        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            QFontDatabase.removeApplicationFont(font_id)
            destination.unlink(missing_ok=True)
            raise ValueError("The selected file does not contain a usable font family.")

        self._registered_font_ids.append(font_id)
        filenames = self._settings_manager.get(self.IMPORTED_FONTS_KEY, [], list)
        filenames.append(destination.name)
        self._settings_manager.set(self.IMPORTED_FONTS_KEY, filenames)
        self._settings_manager.sync()

        return families[0]

    def _unique_destination(self, filename: str) -> Path:
        """Generate a destination path without overwriting an existing font."""
        source = Path(filename)
        destination = self._fonts_directory / source.name
        counter = 1

        while destination.exists():
            destination = self._fonts_directory / f"{source.stem}-{counter}{source.suffix}"
            counter += 1

        return destination
