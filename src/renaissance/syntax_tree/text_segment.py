from typing import Protocol, runtime_checkable


@runtime_checkable
class TextSegment(Protocol):
    """Protocol for anything that represents a text segment.
    A text segment is a consecutive piece, a.k.a. a slice, within a text.
    Instances include comments, whitespace (incl. empty lines), and syntax nodes.

    Read-only access is enforced "as much as possible" by
    exposing only @property getters in the protocol
    """

    @property
    def full_text(self) -> str:
        """The full text that contains the text segment."""
        ...

    @property
    def location(self) -> str:
        """The location of the full text that contains the text segment.
        For example, when text originates from disk the location is a file path.
        """
        ...

    @property
    def start_offset(self) -> int:
        """Start offset of text segment.
        start_offset is an integer in [0, len(full_text)].
        """
        ...

    @property
    def start_line(self) -> int:
        """Start line of text segment - 0 based."""
        ...

    @property
    def start_column(self) -> int:
        """Start column of text segment - 0 based."""
        ...

    @property
    def end_offset(self) -> int:
        """Exclusive end offset of text segment.
        end_offset is an integer in [0, len(full_text)].
        """
        ...

    @property
    def end_line(self) -> int:
        """End line of text segment - 0 based."""
        ...

    @property
    def end_column(self) -> int:
        """End column of text segment - 0 based."""
        ...

    @property
    def text_segment(self) -> str:
        """The text segment is a slice of the full text.
        The text segment is represented by the half-open interval [start_offset, end_offset).
        The segment text is full_text[start_offset:end_offset].
        """
        ...
