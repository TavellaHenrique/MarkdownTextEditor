
import pytest

from markdown_editor.markdown_parser import MarkdownParser


@pytest.fixture
def parser():
    """Provide a Markdown parser instance for each test."""
    return MarkdownParser()


def test_convert_heading_to_html(parser):
    """Verify that Markdown headings are converted to HTML."""
    result = parser.to_html("# Heading Test")

    assert "<h1>Heading Test</h1>" in result


def test_convert_bold_text_to_html(parser):
    """Verify that bold Markdown text is converted to HTML."""
    result = parser.to_html("**Important Text**")

    assert "<strong>Important Text</strong>" in result


def test_convert_italic_text_to_html(parser):
    """Verify that italic Markdown text is converted to HTML."""
    result = parser.to_html("*Italic Text*")

    assert "<em>Italic Text</em>" in result


def test_convert_paragraph_to_html(parser):
    """Verify that paragraphs are converted to HTML."""
    result = parser.to_html("This is a paragraph.")

    assert "<p>This is a paragraph.</p>" in result


def test_convert_unordered_list_to_html(parser):
    """Verify that unordered lists are converted to HTML."""
    result = parser.to_html("- First item\n- Second item")

    assert "<ul>" in result
    assert "<li>First item</li>" in result
    assert "<li>Second item</li>" in result


def test_convert_ordered_list_to_html(parser):
    """Verify that ordered lists are converted to HTML."""
    result = parser.to_html("1. First item\n2. Second item")

    assert "<ol>" in result
    assert "<li>First item</li>" in result
    assert "<li>Second item</li>" in result


def test_convert_inline_code_to_html(parser):
    """Verify that inline code is converted to HTML."""
    result = parser.to_html("Use `print()` to display text.")

    assert "<code>print()</code>" in result


def test_convert_fenced_code_block_to_html(parser):
    """Verify that fenced code blocks are converted to HTML."""
    result = parser.to_html("```python\nprint('Hello')\n```")

    assert "<pre>" in result
    assert '<code class="language-python">' in result
    assert "print(" in result


def test_convert_link_to_html(parser):
    """Verify that Markdown links are converted to HTML."""
    result = parser.to_html("[OpenAI](https://openai.com)")

    assert '<a href="https://openai.com">OpenAI</a>' in result


def test_convert_empty_text_to_html(parser):
    """Verify that empty Markdown input returns an empty string."""
    result = parser.to_html("")

    assert result == ""
