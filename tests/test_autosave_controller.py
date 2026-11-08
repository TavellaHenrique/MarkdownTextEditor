from unittest.mock import Mock

import pytest
from PySide6.QtGui import QTextDocument

from markdown_editor.autosave_controller import AutoSaveController


@pytest.fixture
def document():
    """Provide a document for automatic saving tests."""
    return QTextDocument()


@pytest.fixture
def save_callback():
    """Provide a mocked save callback."""
    return Mock(return_value=True)


def create_controller(document, save_callback, file_path=None, interval=60_000):
    """Create an automatic saving controller for testing."""
    return AutoSaveController(
        document=document,
        get_file_path=lambda: file_path,
        save_callback=save_callback,
        interval=interval,
    )


def test_autosave_controller_initialization(
    qtbot,
    document,
    save_callback,
):
    """Verify that the controller initializes with the default interval."""
    controller = create_controller(document, save_callback)

    assert controller.interval == 60_000
    assert controller.is_active


def test_autosave_does_not_save_new_document(document, save_callback):
    """Verify that documents without a file path are not saved."""
    document.setModified(True)

    controller = create_controller(document, save_callback)

    result = controller.save_if_needed()

    assert result is False
    save_callback.assert_not_called()


def test_autosave_does_not_save_unmodified_document(document, save_callback):
    """Verify that unmodified documents are not saved."""
    controller = create_controller(
        document,
        save_callback,
        file_path="document.md",
    )

    result = controller.save_if_needed()

    assert result is False
    save_callback.assert_not_called()


def test_autosave_saves_modified_document(document, save_callback):
    """Verify that modified documents with a path are saved."""
    document.setModified(True)

    controller = create_controller(
        document,
        save_callback,
        file_path="document.md",
    )

    result = controller.save_if_needed()

    assert result is True
    save_callback.assert_called_once()


def test_autosave_returns_save_failure(document):
    """Verify that failed save operations are reported."""
    save_callback = Mock(return_value=False)
    document.setModified(True)

    controller = create_controller(
        document,
        save_callback,
        file_path="document.md",
    )

    result = controller.save_if_needed()

    assert result is False
    save_callback.assert_called_once()


def test_autosave_timer_can_be_stopped(document, save_callback):
    """Verify that the automatic saving timer can be stopped."""
    controller = create_controller(document, save_callback)

    controller.stop()

    assert not controller.is_active


def test_autosave_timer_can_be_started(
    document,
    save_callback,
):
    """Verify that the automatic saving timer can be restarted."""
    controller = create_controller(document, save_callback)

    controller.stop()
    controller.start()

    assert controller.is_active


def test_autosave_can_be_disabled(document, save_callback):
    """Verify that the automatic saving feature can be disabled."""
    controller = create_controller(document, save_callback)

    controller.set_enabled(False)

    assert controller.is_enabled is False
    assert controller.is_active is False

    result = controller.save_if_needed()

    assert result is False
    save_callback.assert_not_called()


def test_autosave_interval_can_be_changed(document, save_callback):
    """Verify that the timer interval can be updated."""
    controller = create_controller(document, save_callback)

    controller.set_interval(30_000)

    assert controller.interval == 30_000


def test_autosave_rejects_invalid_interval(document, save_callback):
    """Verify that invalid timer intervals are rejected."""
    with pytest.raises(ValueError):
        create_controller(
            document,
            save_callback,
            interval=0,
        )
