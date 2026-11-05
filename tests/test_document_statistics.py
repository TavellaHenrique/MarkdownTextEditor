import pytest

from markdown_editor.document_statistics import (
    DocumentStatistics,
    calculate_document_statistics,
)


def test_calculate_statistics_for_empty_document():
    """Test statistics for an empty document."""
    result = calculate_document_statistics("")

    assert result == DocumentStatistics(
        word_count=0,
        character_count=0,
        character_count_without_whitespace=0,
        line_count=1,
        paragraph_count=0,
        reading_time_minutes=0,
    )


def test_calculate_statistics_for_simple_document():
    """Test statistics for a document containing multiple paragraphs."""
    text = "Hello world!\n\nThis is a test."

    result = calculate_document_statistics(text)

    assert result.word_count == 6
    assert result.character_count == len(text)
    assert result.character_count_without_whitespace == 23
    assert result.line_count == 3
    assert result.paragraph_count == 2
    assert result.reading_time_minutes == 1


def test_calculate_statistics_with_trailing_newline():
    """Test line counting when the document ends with a newline."""
    result = calculate_document_statistics("First line\n")

    assert result.line_count == 2


def test_calculate_statistics_with_custom_reading_speed():
    """Test reading time with a custom reading speed."""
    text = " ".join(["word"] * 450)

    result = calculate_document_statistics(
        text,
        reading_speed=200,
    )

    assert result.reading_time_minutes == 3


def test_calculate_statistics_with_invalid_reading_speed():
    """Test that invalid reading speeds raise an exception."""
    with pytest.raises(ValueError):
        calculate_document_statistics(
            "Some text",
            reading_speed=0,
        )
