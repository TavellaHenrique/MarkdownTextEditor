from markdown_editor.document_outline import DocumentOutline
from markdown_editor.markdown_parser import DocumentHeading


def test_set_headings_creates_hierarchy(qtbot):
    """Test that headings are organized according to their levels."""
    outline = DocumentOutline()
    qtbot.addWidget(outline)

    headings = [
        DocumentHeading(1, "Introduction", 1),
        DocumentHeading(2, "Installation", 3),
        DocumentHeading(3, "Requirements", 5),
        DocumentHeading(2, "Usage", 8),
        DocumentHeading(1, "Conclusion", 12),
    ]

    outline.set_headings(headings)

    assert outline.topLevelItemCount() == 2

    introduction = outline.topLevelItem(0)
    conclusion = outline.topLevelItem(1)

    assert introduction.text(0) == "Introduction"
    assert introduction.childCount() == 2

    installation = introduction.child(0)
    usage = introduction.child(1)

    assert installation.text(0) == "Installation"
    assert installation.childCount() == 1
    assert installation.child(0).text(0) == "Requirements"

    assert usage.text(0) == "Usage"
    assert conclusion.text(0) == "Conclusion"


def test_set_headings_handles_missing_levels(qtbot):
    """Test hierarchy construction when heading levels are skipped."""
    outline = DocumentOutline()
    qtbot.addWidget(outline)

    headings = [
        DocumentHeading(1, "Introduction", 1),
        DocumentHeading(3, "Details", 3),
        DocumentHeading(2, "Installation", 5),
    ]

    outline.set_headings(headings)

    introduction = outline.topLevelItem(0)

    assert introduction.childCount() == 2
    assert introduction.child(0).text(0) == "Details"
    assert introduction.child(1).text(0) == "Installation"


def test_set_headings_stores_source_line(qtbot):
    """Test that each tree item stores its source line."""
    outline = DocumentOutline()
    qtbot.addWidget(outline)

    outline.set_headings(
        [
            DocumentHeading(1, "Introduction", 7),
        ]
    )

    item = outline.topLevelItem(0)

    assert item.data(0, 256) == 7


def test_item_click_emits_heading_line(qtbot):
    """Test that selecting a heading emits its source line."""
    outline = DocumentOutline()
    qtbot.addWidget(outline)

    outline.set_headings(
        [
            DocumentHeading(1, "Introduction", 7),
        ]
    )

    selected_lines = []
    outline.heading_selected.connect(selected_lines.append)

    item = outline.topLevelItem(0)
    outline.itemClicked.emit(item, 0)

    assert selected_lines == [7]


def test_set_empty_headings_clears_tree(qtbot):
    """Test that an empty heading list clears the tree."""
    outline = DocumentOutline()
    qtbot.addWidget(outline)

    outline.set_headings(
        [
            DocumentHeading(1, "Introduction", 1),
        ]
    )

    outline.set_headings([])

    assert outline.topLevelItemCount() == 0
