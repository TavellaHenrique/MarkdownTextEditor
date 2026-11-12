from collections.abc import Callable

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu, QMenuBar, QWidget

ActionConfig = tuple[str, str, Callable[..., None]]


class MenuController:
    """Create and manage the application menus."""

    def __init__(
        self,
        menu_bar: QMenuBar,
        parent: QWidget,
        file_actions: list[ActionConfig],
        edit_actions: list[ActionConfig],
        view_actions: list[ActionConfig],
        theme_names: tuple[str, ...],
        current_theme: str,
        on_theme_changed: Callable[[str], None],
        on_preview_toggled: Callable[[bool], None],
        on_outline_toggled: Callable[[bool], None] | None = None,
        format_actions: list[ActionConfig] | None = None,
        heading_actions: list[ActionConfig] | None = None,
        list_actions: list[ActionConfig] | None = None,
        code_actions: list[ActionConfig] | None = None,
        on_auto_save_toggled: Callable[[bool], None] | None = None,
        auto_save_enabled: bool = True,
        on_auto_save_interval_changed: Callable[[int], None] | None = None,
        auto_save_interval: int = 60_000,
        on_settings_requested: Callable[[], None] | None = None,
    ):
        """Initialize the menu controller."""
        self._menu_bar = menu_bar
        self._parent = parent
        self._theme_actions: dict[str, QAction] = {}
        self._preview_action: QAction | None = None
        self._outline_action: QAction | None = None
        self._auto_save_action: QAction | None = None
        self._settings_action: QAction | None = None

        self._create_file_menu(
            file_actions,
            on_auto_save_toggled,
            auto_save_enabled,
            on_auto_save_interval_changed,
            auto_save_interval,
        )
        self._create_edit_menu(edit_actions)
        self._create_format_menu(
            format_actions or [],
            heading_actions or [],
            list_actions or [],
            code_actions or [],
        )
        self._create_view_menu(
            view_actions,
            theme_names,
            current_theme,
            on_theme_changed,
            on_preview_toggled,
            on_outline_toggled,
        )
        self._create_settings_action(on_settings_requested)

    @property
    def settings_action(self) -> QAction:
        """Return the application settings action."""
        if self._settings_action is None:
            raise RuntimeError("Settings action has not been initialized.")

        return self._settings_action

    def _create_settings_action(
        self,
        callback: Callable[[], None] | None,
    ) -> None:
        """Add the Settings action directly after the View menu."""
        self._settings_action = QAction("Settings", self._parent)
        self._settings_action.setToolTip("Open application settings")

        if callback is not None:
            self._settings_action.triggered.connect(callback)

        self._menu_bar.addAction(self._settings_action)

    @property
    def theme_actions(self) -> dict[str, QAction]:
        """Return the available theme actions."""
        return self._theme_actions

    @property
    def preview_action(self) -> QAction:
        """Return the preview visibility action."""
        if self._preview_action is None:
            raise RuntimeError("Preview action has not been initialized.")

        return self._preview_action

    @property
    def outline_action(self) -> QAction:
        """Return the outline visibility action."""
        if self._outline_action is None:
            raise RuntimeError("Outline action has not been initialized.")

        return self._outline_action

    @property
    def auto_save_action(self) -> QAction:
        """Return the autosave toggle action."""
        if self._auto_save_action is None:
            raise RuntimeError("Autosave action has not been initialized.")

        return self._auto_save_action

    def _create_file_menu(
        self,
        actions: list[ActionConfig],
        on_auto_save_toggled: Callable[[bool], None] | None = None,
        auto_save_enabled: bool = True,
        on_auto_save_interval_changed: Callable[[int], None] | None = None,
        auto_save_interval: int = 60_000,
    ) -> None:
        """Create the File menu."""
        file_menu = self._menu_bar.addMenu("File")
        self._add_actions(file_menu, actions)
        file_menu.addSeparator()

        self._auto_save_action = QAction("Auto Save", self._parent)
        self._auto_save_action.setCheckable(True)
        self._auto_save_action.setChecked(auto_save_enabled)

        if on_auto_save_toggled is not None:
            self._auto_save_action.toggled.connect(on_auto_save_toggled)

        file_menu.addAction(self._auto_save_action)

        if on_auto_save_interval_changed is not None:
            auto_save_interval_menu = file_menu.addMenu("Auto Save Interval")
            interval_values = (15_000, 30_000, 60_000, 120_000)
            interval_group = QActionGroup(self._parent)
            interval_group.setExclusive(True)

            for interval in interval_values:
                interval_action = QAction(f"{interval // 1000} seconds", self._parent)
                interval_action.setCheckable(True)
                interval_action.setChecked(interval == auto_save_interval)
                interval_group.addAction(interval_action)
                interval_action.triggered.connect(
                    lambda checked, value=interval: (
                        on_auto_save_interval_changed(value) if checked else None
                    )
                )
                auto_save_interval_menu.addAction(interval_action)

    def _create_edit_menu(self, actions: list[ActionConfig]) -> None:
        """Create the Edit menu."""
        edit_menu = self._menu_bar.addMenu("Edit")

        self._add_actions(edit_menu, actions[:2])
        edit_menu.addSeparator()

        self._add_actions(edit_menu, actions[2:6])
        edit_menu.addSeparator()

        self._add_actions(edit_menu, actions[6:])

    def _create_format_menu(
        self,
        actions: list[ActionConfig],
        heading_actions: list[ActionConfig],
        list_actions: list[ActionConfig],
        code_actions: list[ActionConfig],
    ) -> None:
        """Create the Format menu and its subgroups."""
        format_menu = self._menu_bar.addMenu("Format")

        self._add_actions(format_menu, actions[:2])

        if actions[2:]:
            format_menu.addSeparator()
            self._add_actions(format_menu, actions[2:])

        if heading_actions:
            format_menu.addSeparator()
            heading_menu = format_menu.addMenu("Heading")
            self._add_actions(heading_menu, heading_actions)

        if code_actions:
            format_menu.addSeparator()
            code_menu = format_menu.addMenu("Code")
            self._add_actions(code_menu, code_actions)

        if list_actions:
            format_menu.addSeparator()
            list_menu = format_menu.addMenu("List")
            self._add_actions(list_menu, list_actions)

        format_menu.addSeparator()

    def _create_view_menu(
        self,
        actions: list[ActionConfig],
        theme_names: tuple[str, ...],
        current_theme: str,
        on_theme_changed: Callable[[str], None],
        on_preview_toggled: Callable[[bool], None],
        on_outline_toggled: Callable[[bool], None] | None,
    ) -> None:
        """Create the View menu and its submenus."""
        view_menu = self._menu_bar.addMenu("View")

        # Create the preview visibility action.
        self._preview_action = QAction("Show Preview", self._parent)
        self._preview_action.setShortcut("Ctrl+P")
        self._preview_action.setCheckable(True)
        self._preview_action.setChecked(True)
        self._preview_action.toggled.connect(on_preview_toggled)

        view_menu.addAction(self._preview_action)

        self._outline_action = QAction("Show Document Outline", self._parent)
        self._outline_action.setShortcut("Ctrl+Shift+O")
        self._outline_action.setCheckable(True)
        self._outline_action.setChecked(True)

        if on_outline_toggled is not None:
            self._outline_action.toggled.connect(on_outline_toggled)

        view_menu.addAction(self._outline_action)

        self._create_theme_menu(
            view_menu,
            theme_names,
            current_theme,
            on_theme_changed,
        )

        view_menu.addSeparator()
        self._add_actions(view_menu, actions)

    def _create_theme_menu(
        self,
        parent_menu: QMenu,
        theme_names: tuple[str, ...],
        current_theme: str,
        on_theme_changed: Callable[[str], None],
    ) -> None:
        """Create the theme selection submenu."""
        theme_menu = parent_menu.addMenu("Theme")

        self._theme_action_group = QActionGroup(self._parent)
        self._theme_action_group.setExclusive(True)

        for theme_name in theme_names:
            display_name = theme_name.replace("_", " ").replace("-", " ").title()

            action = QAction(display_name, self._parent)
            action.setCheckable(True)
            action.setChecked(theme_name == current_theme)

            action.triggered.connect(
                lambda checked, name=theme_name: on_theme_changed(name) if checked else None
            )

            self._theme_action_group.addAction(action)
            theme_menu.addAction(action)

            self._theme_actions[theme_name] = action

    def _add_actions(
        self,
        menu: QMenu,
        actions: list[ActionConfig],
    ) -> None:
        """Add configured actions to a menu."""
        for text, shortcut, callback in actions:
            action = QAction(text, self._parent)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            menu.addAction(action)
