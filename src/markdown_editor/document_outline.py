from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from markdown_editor.markdown_parser import DocumentHeading


class DocumentOutline(QTreeWidget):
    """Display document headings in a hierarchical tree."""

    heading_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setUniformRowHeights(True)

        self.itemClicked.connect(self._on_item_clicked)

    def set_headings(self, headings: list[DocumentHeading]) -> None:
        """Populate the tree with document headings."""
        self.clear()

        # Keep the most recent item for each heading level.
        hierarchy: list[tuple[int, QTreeWidgetItem]] = []

        for heading in headings:
            item = QTreeWidgetItem([heading.title])
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                heading.line_number,
            )

            # Find the closest preceding heading with a lower level.
            while hierarchy and hierarchy[-1][0] >= heading.level:
                hierarchy.pop()

            if hierarchy:
                hierarchy[-1][1].addChild(item)
            else:
                self.addTopLevelItem(item)

            hierarchy.append((heading.level, item))

        self.expandAll()

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Emit the source line of the selected heading."""
        line_number = item.data(0, Qt.ItemDataRole.UserRole)

        if line_number is not None:
            self.heading_selected.emit(line_number)
