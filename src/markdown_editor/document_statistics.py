import math
import re
from dataclasses import dataclass

DEFAULT_READING_SPEED = 200


@dataclass(frozen=True, slots=True)
class DocumentStatistics:
    """Store statistics calculated from a Markdown document."""

    word_count: int
    character_count: int
    character_count_without_whitespace: int
    line_count: int
    paragraph_count: int
    reading_time_minutes: int


def calculate_document_statistics(
    text: str,
    reading_speed: int = DEFAULT_READING_SPEED,
) -> DocumentStatistics:
    """Calculate statistics for the provided document text."""
    if reading_speed <= 0:
        raise ValueError("Reading speed must be greater than zero.")

    words = text.split()

    paragraphs = [
        paragraph
        for paragraph in re.split(
            r"(?:\r\n|\r|\n)[ \t]*(?:\r\n|\r|\n)+",
            text.strip(),
        )
        if paragraph.strip()
    ]

    line_count = max(
        1,
        len(text.splitlines()) + (1 if text.endswith(("\n", "\r")) else 0),
    )

    word_count = len(words)

    reading_time = math.ceil(word_count / reading_speed) if word_count > 0 else 0

    return DocumentStatistics(
        word_count=word_count,
        character_count=len(text),
        character_count_without_whitespace=sum(not character.isspace() for character in text),
        line_count=line_count,
        paragraph_count=len(paragraphs),
        reading_time_minutes=reading_time,
    )
