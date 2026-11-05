from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QToolButton,
    QWidget,
)


class SearchInput(QLineEdit):
    """Search input with keyboard navigation shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Prevent arrow keys from moving the text cursor.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle arrow keys for search navigation."""

        if event.key() == Qt.Key.Key_Down:
            self.parent().next_requested.emit()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Up:
            self.parent().previous_requested.emit()
            event.accept()
            return

        super().keyPressEvent(event)


class FindBar(QFrame):
    """Provide the user interface for text search."""

    search_text_changed = Signal(str)
    previous_requested = Signal()
    next_requested = Signal()
    close_requested = Signal()
    highlight_all_changed = Signal(bool)
    case_sensitive_changed = Signal(bool)
    accent_sensitive_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("findBar")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._create_widgets()
        self._create_layout()
        self._create_options_menu()
        self._connect_signals()
        self._create_shortcuts()

        self.hide()

    def _create_widgets(self):
        """Create the search field and action buttons."""

        self.search_input = SearchInput(self)
        self.search_input.setObjectName("findInput")
        self.search_input.setPlaceholderText("Find")
        self.search_input.setClearButtonEnabled(True)

        # Display the current occurrence and total match count.
        self.match_label = QLabel("0/0")
        self.match_label.setObjectName("matchLabel")
        self.match_label.setMinimumWidth(40)
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_label.setToolTip("Current occurrence / Total occurrences")

        self.previous_button = QToolButton()
        self.previous_button.setObjectName("previousButton")
        self.previous_button.setText("↑")
        self.previous_button.setToolTip("Previous occurrence (Up)")

        self.next_button = QToolButton()
        self.next_button.setObjectName("nextButton")
        self.next_button.setText("↓")
        self.next_button.setToolTip("Next occurrence (Down)")

        self.options_button = QToolButton()
        self.options_button.setObjectName("optionsButton")
        self.options_button.setText("⋮")
        self.options_button.setToolTip("Search options")
        self.options_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.close_button = QToolButton()
        self.close_button.setObjectName("closeButton")
        self.close_button.setText("×")
        self.close_button.setToolTip("Close search (Esc)")

    def _create_layout(self):
        """Arrange the search controls horizontally."""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.match_label)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.options_button)
        layout.addWidget(self.close_button)

    def update_match_indicator(self, current: int, total: int):
        """Update the current occurrence indicator."""
        self.match_label.setText(f"{current} of {total}")

    def _create_options_menu(self):
        """Create the expandable menu with search options."""

        self.options_menu = QMenu(self)

        self.highlight_all_action = QAction(
            "Highlight all matches",
            self,
        )
        self.highlight_all_action.setCheckable(True)
        self.highlight_all_action.setChecked(True)

        self.case_sensitive_action = QAction(
            "Match case",
            self,
        )
        self.case_sensitive_action.setCheckable(True)
        self.case_sensitive_action.setChecked(False)

        self.accent_sensitive_action = QAction(
            "Match accents",
            self,
        )
        self.accent_sensitive_action.setCheckable(True)
        self.accent_sensitive_action.setChecked(True)

        self.options_menu.addAction(self.highlight_all_action)
        self.options_menu.addAction(self.case_sensitive_action)
        self.options_menu.addAction(self.accent_sensitive_action)

        self.options_button.setMenu(self.options_menu)

    def _connect_signals(self):
        """Connect widget events to the component signals."""

        self.search_input.textChanged.connect(self.search_text_changed.emit)

        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.close_button.clicked.connect(self.close_bar)

        self.highlight_all_action.toggled.connect(self.highlight_all_changed.emit)
        self.case_sensitive_action.toggled.connect(self.case_sensitive_changed.emit)
        self.accent_sensitive_action.toggled.connect(self.accent_sensitive_changed.emit)

    def _create_shortcuts(self):
        """Configure keyboard shortcuts available while the bar is visible."""

        self.escape_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Escape),
            self,
        )
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.close_bar)

    def set_theme_colors(self, foreground: str, background: str):
        """Apply theme colors to the search bar and its components."""
        self.setStyleSheet(
            f"""
            #findBar {{
                background-color: {background};
                border: 1px solid {foreground};
                border-radius: 6px;
            }}

            #findBar QLabel,
            #findBar QToolButton {{
                color: {foreground};
                background-color: transparent;
            }}

            #findBar QLineEdit, QToolButton {{
                color: {foreground};
                background-color: transparent;
                border: 1px solid {foreground};
                border-radius: 4px;
                padding: 4px;
            }}

            #findBar QLineEdit::placeholder {{
                color: {foreground};
            }}

            #findBar QToolButton {{
                padding: 2px;
            }}

            #findBar QToolButton:hover {{
                background-color: rgba(128, 128, 128, 40);
                border-radius: 4px;
            }}
            """
        )

    def show_bar(self, selected_text: str = ""):
        """Show the search bar without automatically executing a search."""

        self.search_input.blockSignals(True)
        self.search_input.setText(selected_text)
        self.search_input.blockSignals(False)

        self.show()
        self.search_input.setFocus()

        if selected_text:
            self.search_input.selectAll()

    def close_bar(self):
        """Hide the search bar and notify connected components."""

        self.hide()
        self.close_requested.emit()
