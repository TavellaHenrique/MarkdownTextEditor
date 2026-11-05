from dataclasses import dataclass

from markdown_it import MarkdownIt


@dataclass(frozen=True, slots=True)
class DocumentHeading:
    """Represent a heading extracted from a Markdown document."""

    level: int
    title: str
    line_number: int


class MarkdownParser:
    """Convert Markdown text into HTML and extract document headings."""

    def __init__(self):
        """Initialize the Markdown parser."""
        self._parser = MarkdownIt("commonmark")

    def to_html(self, markdown_text: str) -> str:
        """Convert Markdown text into HTML."""
        return self._parser.render(markdown_text)

    def extract_headings(self, markdown_text: str) -> list[DocumentHeading]:
        """Extract headings and their source line numbers."""
        tokens = self._parser.parse(markdown_text)
        headings = []

        for index, token in enumerate(tokens):
            if token.type != "heading_open":
                continue

            inline_token = tokens[index + 1]

            headings.append(
                DocumentHeading(
                    level=int(token.tag[1]),
                    title=self._extract_plain_text(inline_token),
                    line_number=token.map[0] + 1,
                )
            )

        return headings

    def _extract_plain_text(self, inline_token) -> str:
        """Extract plain text from an inline Markdown token."""
        if not inline_token.children:
            return inline_token.content

        return "".join(
            token.content
            for token in inline_token.children
            if token.type in {"text", "code_inline"}
        )
