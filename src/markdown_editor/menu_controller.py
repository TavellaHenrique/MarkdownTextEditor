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
    ):
        """Initialize the menu controller."""
        self._menu_bar = menu_bar
        self._parent = parent
        self._theme_actions: dict[str, QAction] = {}

        self._create_file_menu(file_actions)
        self._create_edit_menu(edit_actions)
        self._create_format_menu(
            format_actions or [],
            heading_actions or [],
        )
        self._create_view_menu(
            view_actions,
            theme_names,
            current_theme,
            on_theme_changed,
            on_preview_toggled,
            on_outline_toggled,
        )

    @property
    def theme_actions(self) -> dict[str, QAction]:
        """Return the available theme actions."""
        return self._theme_actions

    def _create_file_menu(self, actions: list[ActionConfig]) -> None:
        """Create the File menu."""
        file_menu = self._menu_bar.addMenu("File")
        self._add_actions(file_menu, actions)

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
    ) -> None:
        """Create the Format menu and its heading submenu."""
        format_menu = self._menu_bar.addMenu("Format")

        self._add_actions(format_menu, actions)

        if heading_actions:
            format_menu.addSeparator()
            heading_menu = format_menu.addMenu("Heading")
            self._add_actions(heading_menu, heading_actions)

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

        preview_action = QAction("Show Preview", self._parent)
        preview_action.setShortcut("Ctrl+P")
        preview_action.setCheckable(True)
        preview_action.setChecked(True)
        preview_action.toggled.connect(on_preview_toggled)

        view_menu.addAction(preview_action)

        outline_action = QAction("Show Document Outline", self._parent)
        outline_action.setShortcut("Ctrl+Shift+O")
        outline_action.setCheckable(True)
        outline_action.setChecked(True)

        if on_outline_toggled is not None:
            outline_action.toggled.connect(on_outline_toggled)

        view_menu.addAction(outline_action)

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
                lambda checked, name=theme_name: (
                    on_theme_changed(name) if checked else None
                )
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
