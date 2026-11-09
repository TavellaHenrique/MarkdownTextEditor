import pytest
from PySide6.QtGui import QTextCursor

from markdown_editor.code_editor import CodeEditor


def test_editor_initialization(qtbot):
    """Verify that the editor can be initialized."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    assert editor.toPlainText() == ""


def test_empty_editor_does_not_activate_line_highlight(qtbot):
    """The placeholder should remain visible when the document is empty."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlaceholderText("Out of words?")
    editor.highlight_current_line()

    assert editor.extraSelections() == []


def test_editor_font_size_updates_document_default_font(qtbot):
    """The document default font should scale with editor zoom levels."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.set_font_size(18)

    assert editor.font().pointSize() == 18
    assert editor.document().defaultFont().pointSize() == 18


def test_editor_placeholder_font_follows_editor_zoom(qtbot):
    """The placeholder text should use the same font size as the editor."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlaceholderText("Out of words?")
    editor.set_font_size(20)

    assert editor.font().pointSize() == 20
    assert editor.document().defaultFont().pointSize() == 20


def test_editor_displays_text(qtbot):
    """Verify that the editor displays inserted text."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    expected_text = "# Markdown Editor"
    editor.setPlainText(expected_text)

    assert editor.toPlainText() == expected_text


def test_editor_accepts_multiple_lines(qtbot):
    """Verify that the editor handles multiple lines."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("First line\nSecond line\nThird line")

    assert editor.blockCount() == 3


def test_editor_cursor_position(qtbot):
    """Verify that the cursor can move between lines."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("First line\nSecond line")

    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    assert editor.textCursor().blockNumber() == 1


def test_search_text_finds_all_occurrences(qtbot):
    """Verify that all matching occurrences are found."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("Markdown Markdown Python")

    result = editor.search_text("Markdown")

    assert result == 2
    assert len(editor._search_matches) == 2


def test_search_text_ignores_case_when_disabled(qtbot):
    """Verify case-insensitive search."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("Python python PYTHON")

    result = editor.search_text("python")

    assert result == 3


def test_search_text_respects_case_when_enabled(qtbot):
    """Verify case-sensitive search."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("Python python PYTHON")

    result = editor.search_text(
        "python",
        case_sensitive=True,
    )

    assert result == 1


def test_search_text_ignores_accents_when_disabled(qtbot):
    """Verify accent-insensitive search."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("cafe café")

    result = editor.search_text(
        "cafe",
        accent_sensitive=False,
    )

    assert result == 2


def test_search_text_respects_accents_when_enabled(qtbot):
    """Verify accent-sensitive search."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("cafe café")

    result = editor.search_text("cafe")

    assert result == 1


def test_search_navigation_is_circular(qtbot):
    """Verify navigation wraps around search occurrences."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("test one test two test")

    editor.search_text("test")

    assert editor._current_match_index == 0

    editor.find_previous()
    assert editor._current_match_index == 2

    editor.find_next()
    assert editor._current_match_index == 0


def test_search_text_returns_zero_when_no_match(qtbot):
    """Verify that searches without matches return zero."""

    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.setPlainText("Markdown editor")

    result = editor.search_text("Python")

    assert result == 0
    assert editor._current_match_index == -1


def test_format_bold_wraps_selected_text(qtbot):
    """Verify that bold formatting wraps selected text."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Hello")

    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)

    editor.format_bold()

    assert editor.toPlainText() == "**Hello**"
    assert editor.textCursor().selectedText() == "Hello"


def test_format_italic_inserts_empty_markers(qtbot):
    """Verify that italic formatting inserts markers at the cursor."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Hello")

    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)

    editor.format_italic()

    assert editor.toPlainText() == "* *Hello".replace(" ", "")
    assert editor.textCursor().position() == 1


def test_insert_link_with_selected_text(qtbot):
    """Verify that link insertion preserves selected text."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("OpenAI")

    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)

    editor.insert_link()

    assert editor.toPlainText() == '[OpenAI](url "title on hover")'
    assert editor.textCursor().selectedText() == "url"


def test_insert_link_without_selection(qtbot):
    """Verify that link insertion creates editable placeholders."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.insert_link()

    assert editor.toPlainText() == '[text](url "title on hover")'
    assert editor.textCursor().selectedText() == "text"


def test_insert_line_break_inserts_html_break(qtbot):
    """Verify that a line break inserts an HTML break tag."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.insert_line_break()

    assert editor.toPlainText() == "<br>"


def test_insert_hidden_comment_inserts_markdown_comment(qtbot):
    """Verify that a markdown hidden comment is inserted."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.insert_hidden_comment()

    assert editor.toPlainText() == "[hidden comment]: #"


def test_insert_blockquote_prefixes_selected_lines(qtbot):
    """Verify that the selected text is converted into a Markdown blockquote."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("First line\nSecond line")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len(editor.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_blockquote()

    assert editor.toPlainText() == "> First line\n> Second line"


def test_insert_inline_code_wraps_selection(qtbot):
    """Verify that inline code wraps a selection in backticks."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("print(1)")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len("print(1)"), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_inline_code()

    assert editor.toPlainText() == "`print(1)`"


def test_insert_horizontal_rule_adds_markdown_divider(qtbot):
    """Verify that a horizontal rule is inserted as a Markdown separator."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.insert_horizontal_rule()

    assert editor.toPlainText() == "---"


def test_insert_fenced_code_block_adds_triple_backticks(qtbot):
    """Verify that fenced code blocks are inserted with opening and closing markers."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.insert_fenced_code_block()

    assert editor.toPlainText() == "```\n\n```"


def test_insert_ordered_list_inserts_markdown_list(qtbot, monkeypatch):
    """Verify that ordered list insertion asks for the length and generates numbers."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    monkeypatch.setattr(
        "markdown_editor.code_editor.QInputDialog.getInt",
        lambda *args, **kwargs: (3, True),
    )

    editor.insert_ordered_list()

    assert editor.toPlainText() == "1. \n2. \n3. "


def test_insert_unordered_list_inserts_markdown_list(qtbot, monkeypatch):
    """Verify that unordered list insertion asks for the length and creates markers."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    monkeypatch.setattr(
        "markdown_editor.code_editor.QInputDialog.getInt",
        lambda *args, **kwargs: (3, True),
    )

    editor.insert_unordered_list()

    assert editor.toPlainText() == "- \n- \n- "


def test_insert_ordered_list_itemizes_existing_line_content(qtbot, monkeypatch):
    """Verify that an existing line is transformed into list items instead of appended."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Existing line")

    monkeypatch.setattr(
        "markdown_editor.code_editor.QInputDialog.getInt",
        lambda *args, **kwargs: (3, True),
    )

    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    editor.insert_ordered_list()

    assert editor.toPlainText() == "1. Existing line\n2. \n3. "


def test_insert_ordered_list_itemizes_selected_multiple_lines(qtbot):
    """Verify that a multi-line selection is converted to ordered items without prompting."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("First line\nSecond line\nThird line")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len("First line\nSecond line\nThird line"), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_ordered_list()

    assert editor.toPlainText() == "1. First line\n2. Second line\n3. Third line"


def test_insert_ordered_list_reenumerates_selected_list_items(qtbot):
    """Verify that a selection already formatted as a list is re-enumerated instead of nested."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("1. First\n2. Second\n3. Third")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len(editor.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_ordered_list()

    assert editor.toPlainText() == "1. First\n2. Second\n3. Third"


def test_insert_unordered_list_removes_markers_from_selected_list_items(qtbot):
    """Verify that unordered list conversion removes existing list markers from selected items."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("1. First\n2. Second\n3. Third")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len(editor.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_unordered_list()

    assert editor.toPlainText() == "- First\n- Second\n- Third"


def test_insert_ordered_list_handles_utf16_selection_positions(qtbot):
    """Verify that list insertion is safe when selections use UTF-16 cursor positions."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Café\nMúsica")

    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len(editor.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.insert_ordered_list()

    assert editor.toPlainText() == "1. Café\n2. Música"


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (1, "# Heading"),
        (2, "## Heading"),
        (3, "### Heading"),
        (4, "#### Heading"),
        (5, "##### Heading"),
        (6, "###### Heading"),
    ],
)
def test_set_heading_level(qtbot, level, expected):
    """Verify that heading levels are applied correctly."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Heading")

    editor.set_heading_level(level)

    assert editor.toPlainText() == expected


def test_set_heading_level_replaces_existing_level(qtbot):
    """Verify that applying a heading replaces the existing level."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("## Existing heading")

    editor.set_heading_level(4)

    assert editor.toPlainText() == "#### Existing heading"


def test_set_heading_level_rejects_invalid_level(qtbot):
    """Verify that invalid heading levels raise an exception."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    with pytest.raises(ValueError):
        editor.set_heading_level(7)


def test_format_bold_removes_existing_formatting(qtbot):
    """Verify that bold formatting can be removed."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("**Hello**")

    cursor = editor.textCursor()
    cursor.setPosition(2)
    cursor.setPosition(7, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.format_bold()

    assert editor.toPlainText() == "Hello"
    assert editor.textCursor().selectedText() == "Hello"


def test_format_bold_removes_delimiters_inside_selection(qtbot):
    """Verify that bold delimiters inside the selection are removed."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("**Hello**")

    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)

    editor.format_bold()

    assert editor.toPlainText() == "Hello"


def test_format_italic_does_not_remove_bold_formatting(qtbot):
    """Verify that italic formatting does not remove bold delimiters."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("**Hello**")

    cursor = editor.textCursor()
    cursor.setPosition(2)
    cursor.setPosition(7, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    editor.format_italic()

    assert editor.toPlainText() == "***Hello***"


@pytest.mark.parametrize(
    ("text", "format_method", "expected"),
    [
        ("*example*", "format_bold", "***example***"),
        ("**example**", "format_italic", "***example***"),
        ("***example***", "format_bold", "*example*"),
        ("***example***", "format_italic", "**example**"),
    ],
)
def test_toggle_combined_formatting(
    qtbot,
    text,
    format_method,
    expected,
):
    """Verify that bold and italic formatting can be combined and toggled."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText(text)

    cursor = editor.textCursor()
    cursor.setPosition(len(text) // 2 - len("example") // 2)
    cursor.setPosition(
        cursor.position() + len("example"),
        QTextCursor.MoveMode.KeepAnchor,
    )
    editor.setTextCursor(cursor)

    getattr(editor, format_method)()

    assert editor.toPlainText() == expected


def test_format_bold_on_entire_document(qtbot):
    """Verify bold formatting works when the entire document is selected."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("First line\nSecond line")

    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)

    editor.format_bold()

    assert editor.toPlainText() == "**First line\nSecond line**"
    assert editor.textCursor().selectedText() == "First line\u2029Second line"


def test_format_italic_on_entire_document(qtbot):
    """Verify italic formatting works when the entire document is selected."""
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("First line\nSecond line")

    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)

    editor.format_italic()

    assert editor.toPlainText() == "*First line\nSecond line*"


def test_set_font_size(qtbot):
    """Verify that the editor font size can be changed."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.set_font_size(18)

    assert editor.font_size == 18


def test_set_font_size_respects_maximum(qtbot):
    """Verify that the font size cannot exceed the maximum."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.set_font_size(CodeEditor.MAX_FONT_SIZE + 10)

    assert editor.font_size == CodeEditor.MAX_FONT_SIZE


def test_set_font_size_respects_minimum(qtbot):
    """Verify that the font size cannot go below the minimum."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    editor.set_font_size(CodeEditor.MIN_FONT_SIZE - 10)

    assert editor.font_size == CodeEditor.MIN_FONT_SIZE
