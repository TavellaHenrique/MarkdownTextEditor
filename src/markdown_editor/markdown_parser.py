from markdown_it import MarkdownIt


class MarkdownParser:
    """Convert Markdown text into HTML"""

    def __init__(self):
        # Initialize the Markdown parser with common Markdown features
        self._parser = MarkdownIt("commonmark")

    def to_html(self, markdown_text: str) -> str:
        """Convert Markdown text into HTML"""

        return self._parser.render(markdown_text)
