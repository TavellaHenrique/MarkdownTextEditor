from PySide6.QtGui import QTextCursor

from markdown_editor.code_editor import CodeEditor


def test_editor_initialization(qtbot):
    """Verify that the editor can be initialized."""
    editor = CodeEditor()
    qtbot.addWidget(editor)

    assert editor.toPlainText() == ""


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
