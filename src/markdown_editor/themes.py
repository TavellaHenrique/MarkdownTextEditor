
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Store the visual configuration of an application theme."""

    application_stylesheet: str
    background: str
    foreground: str
    code_background: str
    code_foreground: str


LIGHT_THEME = Theme(
    application_stylesheet="""
        QMainWindow {
            background-color: #f5f5f5;
        }

        QPlainTextEdit, QTextBrowser {
            background-color: #ffffff;
            color: #242424;
            border: 1px solid #d0d0d0;
            padding: 8px;
            font-size: 14px;
        }

        QMenuBar {
            background-color: #eeeeee;
            color: #242424;
        }

        QMenuBar::item:selected {
            background-color: #dcdcdc;
        }

        QStatusBar {
            background-color: #eeeeee;
            color: #555555;
        }
    """,
    background="#ffffff",
    foreground="#242424",
    code_background="#ff2424",
    code_foreground="#CECECE",
)

DARK_THEME = Theme(
    application_stylesheet="""
        QMainWindow {
            background-color: #202124;
        }

        QPlainTextEdit, QTextBrowser {
            background-color: #292a2d;
            color: #e8eaed;
            border: 1px solid #44464a;
            padding: 8px;
            font-size: 14px;
        }

        QMenuBar {
            background-color: #292a2d;
            color: #e8eaed;
        }

        QMenuBar::item:selected {
            background-color: #44464a;
        }

        QStatusBar {
            background-color: #292a2d;
            color: #bdc1c6;
        }
    """,
    background="#292a2d",
    foreground="#e8eaed",
    code_background="#d41010",
    code_foreground="#f1f3f4",
)


THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


PREVIEW_CSS = """
    body {
        font-family: Arial, sans-serif;
        font-size: 15px;
        line-height: 1.6;
        max-width: 900px;
        margin: 24px auto;
        padding: 0 20px;
    }

    h1, h2, h3, h4 {
        margin-top: 24px;
        margin-bottom: 12px;
    }

    p {
        margin-bottom: 16px;
    }

    code {
        padding: 2px 5px;
        border-radius: 4px;
    }

    pre {
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
    }

    pre code {
        background-color: transparent;
        color: inherit;
        padding: 0;
    }

    blockquote {
        border-left: 4px solid #888888;
        margin-left: 0;
        padding-left: 16px;
        color: #888888;
    }

    img {
        max-width: 100%;
    }
"""


def build_preview_html(markdown_html: str, theme: Theme) -> str:
    """Build the preview HTML using the selected theme."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            {PREVIEW_CSS}

            body {{
                background-color: {theme.background};
                color: {theme.foreground};
            }}

            code, pre, pre code {{
                background-color: {theme.code_background};
                color: {theme.code_foreground};
            }}
        </style>
    </head>
    <body>
        {markdown_html}
    </body>
    </html>
    """
