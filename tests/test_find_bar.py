
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from markdown_editor.find_bar import FindBar


def test_find_bar_initialization(qtbot):
    """Verify that the search bar initializes correctly."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    assert find_bar.search_input is not None
    assert find_bar.previous_button is not None
    assert find_bar.next_button is not None
    assert not find_bar.isVisible()


def test_show_bar_prefills_selected_text_without_search(qtbot):
    """Verify that selected text is prefilled without triggering a search."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    search_spy = QSignalSpy(find_bar.search_text_changed)

    find_bar.show_bar("Markdown")

    assert find_bar.isVisible()
    assert find_bar.search_input.text() == "Markdown"
    assert search_spy.count() == 0


def test_search_input_emits_text_changed(qtbot):
    """Verify that editing the search field emits a signal."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    search_spy = QSignalSpy(find_bar.search_text_changed)

    find_bar.search_input.setText("Python")

    assert search_spy.count() == 1
    assert search_spy.at(0)[0] == "Python"


def test_navigation_buttons_emit_signals(qtbot):
    """Verify that navigation buttons emit their respective signals."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    next_spy = QSignalSpy(find_bar.next_requested)
    previous_spy = QSignalSpy(find_bar.previous_requested)

    qtbot.mouseClick(find_bar.next_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(find_bar.previous_button, Qt.MouseButton.LeftButton)

    assert next_spy.count() == 1
    assert previous_spy.count() == 1


def test_search_options_emit_signals(qtbot):
    """Verify that changing search options emits signals."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    highlight_spy = QSignalSpy(find_bar.highlight_all_changed)
    case_spy = QSignalSpy(find_bar.case_sensitive_changed)
    accent_spy = QSignalSpy(find_bar.accent_sensitive_changed)

    find_bar.highlight_all_action.setChecked(True)
    find_bar.case_sensitive_action.setChecked(True)
    find_bar.accent_sensitive_action.setChecked(False)

    assert highlight_spy.count() == 1
    assert case_spy.count() == 1
    assert accent_spy.count() == 1


def test_close_bar_hides_widget_and_emits_signal(qtbot):
    """Verify that closing the search bar hides it and emits a signal."""
    find_bar = FindBar()
    qtbot.addWidget(find_bar)

    close_spy = QSignalSpy(find_bar.close_requested)

    find_bar.show_bar()
    find_bar.close_bar()

    assert not find_bar.isVisible()
    assert close_spy.count() == 1
