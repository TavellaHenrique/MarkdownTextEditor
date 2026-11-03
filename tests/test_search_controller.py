import pytest
from PySide6.QtWidgets import QStatusBar

from markdown_editor.code_editor import CodeEditor
from markdown_editor.find_bar import FindBar
from markdown_editor.search_controller import SearchController


@pytest.fixture
def search_controller(qtbot):
    """Create a search controller with its dependencies."""
    editor = CodeEditor()
    find_bar = FindBar(editor)
    status_bar = QStatusBar()

    qtbot.addWidget(editor)
    qtbot.addWidget(find_bar)
    qtbot.addWidget(status_bar)

    controller = SearchController(
        editor=editor,
        find_bar=find_bar,
        status_bar=status_bar,
    )

    editor.setPlainText("Python is useful. Python is versatile.")
    find_bar.search_input.setText("Python")

    return controller, editor, find_bar, status_bar


def test_update_search_finds_occurrences(search_controller):
    """Find all matching occurrences."""
    controller, editor, _, _ = search_controller

    controller.update_search()

    assert editor.match_count == 2
    assert editor.current_match_number == 1


def test_find_next_navigates_to_next_occurrence(search_controller):
    """Navigate to the next matching occurrence."""
    controller, editor, _, _ = search_controller

    controller.update_search()
    controller.find_next()

    assert editor.current_match_number == 2


def test_find_previous_wraps_to_last_occurrence(search_controller):
    """Wrap to the last occurrence when navigating backwards."""
    controller, editor, _, _ = search_controller

    controller.update_search()
    controller.find_previous()

    assert editor.current_match_number == 2


def test_clear_search_removes_occurrences(search_controller):
    """Clear search results and reset the occurrence indicator."""
    controller, editor, _, _ = search_controller

    controller.update_search()
    controller.clear_search()

    assert editor.match_count == 0
    assert editor.current_match_number == 0


def test_update_search_displays_no_results_message(search_controller):
    """Display a message when no occurrences are found."""
    controller, _, find_bar, status_bar = search_controller

    find_bar.search_input.setText("Java")
    controller.update_search()

    assert status_bar.currentMessage() == "No results found"
