from markdown_editor.themes import THEMES, Theme


class ThemeController:
    """Manage available themes and the currently selected theme."""

    def __init__(
        self,
        themes: dict[str, Theme] | None = None,
        initial_theme: str = "dark",
    ):
        """Initialize the theme registry and selected theme."""
        self._themes = dict(themes if themes is not None else THEMES)
        self._current_theme_name = ""

        self.set_theme(initial_theme)

    @property
    def available_themes(self) -> tuple[str, ...]:
        """Return the names of available themes."""
        return tuple(self._themes)

    @property
    def current_theme_name(self) -> str:
        """Return the name of the currently selected theme."""
        return self._current_theme_name

    @property
    def current_theme(self) -> Theme:
        """Return the currently selected theme configuration."""
        return self._themes[self._current_theme_name]

    def set_theme(self, theme_name: str) -> Theme:
        """Select a theme by its registered name."""
        if theme_name not in self._themes:
            raise ValueError(f"Unknown theme: {theme_name}")

        self._current_theme_name = theme_name

        return self.current_theme
