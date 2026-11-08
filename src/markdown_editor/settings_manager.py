from typing import Any

from PySide6.QtCore import QSettings


class SettingsManager:
    """Manage persistent application settings."""

    ORGANIZATION_NAME = "MarkdownTextEditor"
    APPLICATION_NAME = "MarkdownTextEditor"

    DEFAULTS = {
        "appearance/theme": "dark",
        "editor/font_size": 14,
        "preview/visible": True,
        "outline/visible": True,
    }

    def __init__(self, settings: QSettings | None = None) -> None:
        """Initialize the settings manager."""
        self._settings = settings or QSettings(
            self.ORGANIZATION_NAME,
            self.APPLICATION_NAME,
        )

    def get(
        self,
        key: str,
        default: Any = None,
        value_type: type | None = None,
    ) -> Any:
        """Retrieve a setting, using its default value when necessary."""
        if default is None:
            default = self.DEFAULTS.get(key)

        if value_type is None:
            return self._settings.value(key, default)

        return self._settings.value(key, default, type=value_type)

    def set(self, key: str, value: Any) -> None:
        """Store a setting."""
        self._settings.setValue(key, value)

    def contains(self, key: str) -> bool:
        """Check whether a setting exists."""
        return self._settings.contains(key)

    def remove(self, key: str) -> None:
        """Remove a setting."""
        self._settings.remove(key)

    def sync(self) -> None:
        """Synchronize settings with persistent storage."""
        self._settings.sync()
