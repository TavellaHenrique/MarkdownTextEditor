import pytest
from PySide6.QtCore import QSettings

from markdown_editor.settings_manager import SettingsManager


@pytest.fixture
def settings_manager(tmp_path):
    """Create a settings manager using temporary storage."""
    settings = QSettings(
        str(tmp_path / "settings.ini"),
        QSettings.Format.IniFormat,
    )

    return SettingsManager(settings)


def test_get_default_values(settings_manager):
    """Verify that default values are returned."""
    assert settings_manager.get("appearance/theme") == "dark"
    assert settings_manager.get("editor/font_size") == 14
    assert settings_manager.get("preview/visible") is True


def test_set_and_get_value(settings_manager):
    """Verify that settings can be stored and retrieved."""
    settings_manager.set("appearance/theme", "light")

    assert settings_manager.get("appearance/theme") == "light"


def test_get_value_with_explicit_type(settings_manager):
    """Verify that values can be retrieved with a specific type."""
    settings_manager.set("editor/font_size", "18")

    assert (
        settings_manager.get(
            "editor/font_size",
            value_type=int,
        )
        == 18
    )


def test_contains_existing_setting(settings_manager):
    """Verify that existing settings can be detected."""
    settings_manager.set("appearance/theme", "light")

    assert settings_manager.contains("appearance/theme")


def test_remove_setting(settings_manager):
    """Verify that settings can be removed."""
    settings_manager.set("appearance/theme", "light")
    settings_manager.remove("appearance/theme")

    assert not settings_manager.contains("appearance/theme")
    assert settings_manager.get("appearance/theme") == "dark"


def test_settings_persistence(settings_manager):
    """Verify that settings survive manager recreation."""
    settings_manager.set("appearance/theme", "light")
    settings_manager.sync()

    new_manager = SettingsManager(settings_manager._settings)

    assert new_manager.get("appearance/theme") == "light"
