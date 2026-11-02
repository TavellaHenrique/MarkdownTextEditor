from markdown_editor.markdown_parser import MarkdownParser

def test_convert_heading_to_html():
    """Verify that Markdown headings are converted to HTML"""

    parser = MarkdownParser()

    result = parser.to_html("# Heading Test")

    assert "<h1>Heading Test</h1>" in result

def test_convert_bold_text_to_html():
    """Verify that Markdown bold text is converted to HTML"""

    parser = MarkdownParser()

    result = parser.to_html("**Important Text**")

    assert "<strong>Important Text</strong>" in result

def test_convert_unordered_list_to_html():
    """Verify that Markdown unordered lists are converted to HTML"""

    parser = MarkdownParser()

    result = parser.to_html("- First item\n- Second item")

    assert "<ul>" in result
    assert "<li>First item</li>" in result
    assert "<li>Second item</li>" in result
