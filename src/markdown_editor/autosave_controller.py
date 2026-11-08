from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QTextDocument


class AutoSaveController(QObject):
    """Manage automatic document saving."""

    DEFAULT_INTERVAL = 60_000

    def __init__(
        self,
        document: QTextDocument,
        get_file_path: Callable[[], Path | None],
        save_callback: Callable[[], bool],
        interval: int = DEFAULT_INTERVAL,
        enabled: bool = True,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the automatic saving controller."""
        super().__init__(parent)

        if interval <= 0:
            raise ValueError("Interval must be greater than zero.")

        self._document = document
        self._get_file_path = get_file_path
        self._save_callback = save_callback
        self._enabled = enabled

        self._timer = QTimer(self)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self.save_if_needed)

        if self._enabled:
            self._timer.start()

    @property
    def interval(self) -> int:
        """Return the current timer interval in milliseconds."""
        return self._timer.interval()

    @property
    def is_active(self) -> bool:
        """Check whether automatic saving is active."""
        return self._timer.isActive()

    @property
    def is_enabled(self) -> bool:
        """Check whether automatic saving is enabled."""
        return self._enabled

    def start(self) -> None:
        """Start automatic saving."""
        self._enabled = True
        self._timer.start()

    def stop(self) -> None:
        """Stop automatic saving."""
        self._enabled = False
        self._timer.stop()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic saving."""
        self._enabled = enabled

        if enabled:
            self._timer.start()
        else:
            self._timer.stop()

    def set_interval(self, interval: int) -> None:
        """Update the automatic saving interval."""
        if interval <= 0:
            raise ValueError("Interval must be greater than zero.")

        self._timer.setInterval(interval)

    def save_if_needed(self) -> bool:
        """Save the document when it has a path and unsaved changes."""
        file_path = self._get_file_path()

        # Do not save new documents without an assigned path.
        if file_path is None:
            return False

        # Skip documents without unsaved changes.
        if not self._document.isModified():
            return False

        return self._save_callback()
