
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
