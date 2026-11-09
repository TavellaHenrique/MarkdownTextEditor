import re
from dataclasses import asdict, dataclass
from importlib.resources import files
from string import Template

from markdown_editor.typography import (
    PREVIEW_FONT_FAMILY,
    PREVIEW_FONT_SIZE,
)


@dataclass(frozen=True)
class Theme:
    """Store the visual configuration of an application theme."""

    background: str
    foreground: str
    code_background: str
    code_foreground: str
    border: str
    menu_background: str
    menu_selected: str
    muted_foreground: str
    link: str
    link_hover: str
    gutter_background: str
    gutter_foreground: str
    current_line_background: str
    search_highlight: str
    current_match: str


LIGHT_THEME = Theme(
    background="#f5f5f5",
    foreground="#242424",
    code_background="#ffffff",
    code_foreground="#242424",
    border="#d0d0d0",
    menu_background="#eeeeee",
    menu_selected="#dcdcdc",
    muted_foreground="#666666",
    link="#2563eb",
    link_hover="#1d4ed8",
    gutter_background="#eeeeee",
    gutter_foreground="#666666",
    current_line_background="#f1f5f9",
    search_highlight="#6eb4d4",
    current_match="#7371e0",
)

DARK_THEME = Theme(
    background="#202124",
    foreground="#e8eaed",
    code_background="#292a2d",
    code_foreground="#e8eaed",
    border="#44464a",
    menu_background="#292a2d",
    menu_selected="#44464a",
    muted_foreground="#9aa0a6",
    link="#8ab4f8",
    link_hover="#d2e3fc",
    gutter_background="#292a2d",
    gutter_foreground="#9aa0a6",
    current_line_background="#283c57",
    search_highlight="#E07D7D",
    current_match="#e4713c",
)

THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def _read_style_file(filename: str) -> str:
    """Read a stylesheet packaged with the application."""
    style_path = files("markdown_editor").joinpath(
        "styles",
        filename,
    )

    return style_path.read_text(encoding="utf-8")


def load_application_stylesheet(theme: Theme) -> str:
    """Load the Qt stylesheet using the selected theme."""
    stylesheet = _read_style_file("application.qss")

    return Template(stylesheet).substitute(asdict(theme))


def load_preview_css() -> str:
    """Load the Markdown preview stylesheet."""
    return _read_style_file("preview.css")


def build_preview_html(markdown_html: str, theme: Theme) -> str:
    """Build the Markdown preview using the selected theme."""
    preview_css = load_preview_css()

    theme_variables = {
        "font-family": PREVIEW_FONT_FAMILY,
        "font-size": f"{PREVIEW_FONT_SIZE}px",
        "background": theme.background,
        "foreground": theme.foreground,
        "code-background": theme.code_background,
        "code-foreground": theme.code_foreground,
        "muted-foreground": theme.muted_foreground,
        "link-color": theme.link,
        "link-hover-color": theme.link_hover,
    }

    for name, value in theme_variables.items():
        preview_css = preview_css.replace(f"var(--{name})", value)

    css_variables = "\n".join(f"    --{name}: {value};" for name, value in theme_variables.items())

    preview_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            :root {{
{css_variables}
            }}

            {preview_css}
        </style>
    </head>
    <body>
        {markdown_html}
    </body>
    </html>
    """

    anchor_style = (
        f"color: {theme.link}; "
        f"text-decoration: underline; "
        f"text-decoration-color: {theme.link_hover};"
    )

    return re.sub(
        r"<a\s+",
        f'<a style="{anchor_style}" ',
        preview_html,
        count=1,
    )
