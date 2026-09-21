"""Tests for the TextSegment offset/location conversions."""

import bisect

import pytest
from hypothesis import given
from hypothesis import strategies as st

from renaissance.syntax_tree.text_segment import TextSegment
from test.syntax_tree.infra_text_segment import (
    assert_valid_text_segment,
    line_starts_from_lines,
    location_to_offset,
    offset_to_location,
    split_lines_with_newlines,
)


class AutoTextSegment:
    """Reference test implementation: construct with offsets; derive (line, column) from full_text boundaries."""

    def __init__(
        self,
        full_text: str,
        start_offset: int,
        end_offset: int,
        location: str = "<memory>",
    ) -> None:
        """AI: Build a reference text segment whose line/column are derived from the given offsets."""
        self._full_text = full_text
        self._location = location
        self._start_offset = start_offset
        self._end_offset = end_offset

        def offset_to_line_col(off: int) -> tuple[int, int]:
            # Map an offset (slice boundary) to (line, column), both 0-based.
            # This supports off in [0, len(full_text)].
            line = 0
            line_start = 0

            # Scan characters strictly before 'off'
            for i, ch in enumerate(full_text):
                if i >= off:
                    break
                if ch == "\n":
                    line += 1
                    line_start = i + 1

            col = off - line_start
            return line, col

        self._start_line, self._start_column = offset_to_line_col(start_offset)
        self._end_line, self._end_column = offset_to_line_col(end_offset)

    # --- Protocol properties ---
    @property
    def full_text(self) -> str:
        """AI: Return the full source text."""
        return self._full_text

    @property
    def location(self) -> str:
        """AI: Return the segment's source location."""
        return self._location

    @property
    def start_line(self) -> int:
        """AI: Return the segment's 0-based start line."""
        return self._start_line

    @property
    def start_column(self) -> int:
        """AI: Return the segment's 0-based start column."""
        return self._start_column

    @property
    def start_offset(self) -> int:
        """AI: Return the segment's start offset."""
        return self._start_offset

    @property
    def end_line(self) -> int:
        """AI: Return the segment's 0-based end line."""
        return self._end_line

    @property
    def end_column(self) -> int:
        """AI: Return the segment's 0-based end column."""
        return self._end_column

    @property
    def end_offset(self) -> int:
        """AI: Return the segment's end offset."""
        return self._end_offset

    @property
    def text_segment(self) -> str:
        """AI: Return the text slice between start_offset and end_offset."""
        return self._full_text[self._start_offset : self._end_offset]


class MissingProperty:
    """Deliberately does NOT satisfy the protocol structurally."""

    @property
    def full_text(self) -> str:
        """AI: Return a dummy full_text value (this class deliberately omits the rest of the protocol)."""
        return "x"


class BadTypesButProtocolLike:
    """Has all required attributes/properties so runtime protocol check passes.

    Types are wrong, so assert_valid_text_segment should fail.
    """

    @property
    def full_text(self):  # not str
        """AI: Return a value of the wrong type (int) for full_text, to trigger a validation failure."""
        return 123

    @property
    def location(self):  # not str
        """AI: Return a value of the wrong type (None) for location, to trigger a validation failure."""
        return None

    @property
    def start_line(self):  # not int
        """AI: Return a value of the wrong type (str) for start_line, to trigger a validation failure."""
        return "hello"

    @property
    def start_column(self):  # not int
        """AI: Return a value of the wrong type (str) for start_column, to trigger a validation failure."""
        return "hello"

    @property
    def start_offset(self):  # not int
        """AI: Return a value of the wrong type (str) for start_offset, to trigger a validation failure."""
        return "hello"

    @property
    def end_line(self):  # not int
        """AI: Return a value of the wrong type (str) for end_line, to trigger a validation failure."""
        return "hello"

    @property
    def end_column(self):  # not int
        """AI: Return a value of the wrong type (str) for end_column, to trigger a validation failure."""
        return "hello"

    @property
    def end_offset(self):  # not int
        """AI: Return a value of the wrong type (str) for end_offset, to trigger a validation failure."""
        return "hello"

    @property
    def text_segment(self):  # not str
        """AI: Return a value of the wrong type (int) for text_segment, to trigger a validation failure."""
        return 456


class InconsistentTextSlice(AutoTextSegment):
    """Matches all numbers, but lies about text_segment."""

    @property
    def text_segment(self) -> str:
        """AI: Return a fixed, deliberately-wrong text_segment value to trigger a validation failure."""
        return "NOT THE SLICE"


class InconsistentOffsets(AutoTextSegment):
    """Offsets present, but line/col purposely inconsistent with boundaries."""

    def __init__(
        self,
        full_text: str,
        start_offset: int,
        end_offset: int,
        location: str = "<memory>",
    ) -> None:
        """AI: Build a text segment whose line/column are deliberately inconsistent with its offsets."""
        super().__init__(full_text, start_offset, end_offset, location)
        # break consistency intentionally
        self._start_column += 1


# ---------------------------
# Structural protocol tests
# ---------------------------


def test_runtime_checkable_protocol_accepts_structural_implementation() -> None:
    """AI: Assert a structurally-conforming object is recognized as a TextSegment via isinstance."""
    seg = AutoTextSegment("abc", 0, 1)
    assert isinstance(seg, TextSegment)


def test_runtime_checkable_protocol_rejects_missing_members() -> None:
    """AI: Assert an object missing required members is rejected by isinstance against TextSegment."""
    seg = MissingProperty()
    assert not isinstance(seg, TextSegment)


# ---------------------------
# Positive semantic tests
# ---------------------------


@pytest.mark.parametrize(
    "text,start,end,expected_slice",
    [
        ("", 0, 0, ""),  # empty full text
        ("a", 0, 1, "a"),  # segment equal full text
        ("\n", 0, 1, "\n"),  # empty line
        ("\n", 1, 1, ""),  # empty last line
        ("ab", 0, 0, ""),  # empty slice before text
        ("ab", 1, 1, ""),  # empty slice inside text
        ("ab", 2, 2, ""),  # empty slice after text
        ("abc", 0, 1, "a"),
        ("abc", 1, 2, "b"),
        ("abc", 2, 3, "c"),
        ("abc", 0, 3, "abc"),  # segment is full text
        ("ab\ncd\nef", 3, 6, "cd\n"),  # segment is second line
        ("ab\ncd\nef", 1, 5, "b\ncd"),  # spans newline and into next line
        ("ab\ncd\nef", 2, 3, "\n"),  # selects newline character
        ("ab\ncd\nef", 3, 4, "c"),  # beginning of line 1
        ("ab\ncd\nef", 6, 8, "ef"),  # last line
    ],
)
def test_assert_valid_text_segment_accepts_semantically_correct_segments(text: str, start: int, end: int, expected_slice: str) -> None:
    """AI: Assert assert_valid_text_segment accepts segments whose text_segment matches the expected slice."""
    seg = AutoTextSegment(text, start, end)
    assert seg.text_segment == expected_slice
    assert_valid_text_segment(seg)


# ---------------------------
# Negative semantic tests
# ---------------------------


def test_validator_rejects_wrong_types_even_if_protocol_like() -> None:
    """AI: Assert assert_valid_text_segment rejects a structurally-protocol-like object with wrong property types."""
    seg = BadTypesButProtocolLike()
    # runtime protocol check likely passes (structural), but validator must fail
    assert isinstance(seg, TextSegment)
    with pytest.raises(
        AssertionError,
        match=r"^Unexpected instance for property full_text '.*'\. Expected 'str'\.$",
    ):
        assert_valid_text_segment(seg)


def test_validator_rejects_start_offset_greater_than_end_offset() -> None:
    """AI: Assert assert_valid_text_segment rejects a segment whose start_offset exceeds its end_offset."""
    seg = AutoTextSegment("abc", 2, 1)
    with pytest.raises(AssertionError, match=r"^Property end_offset before start_offset: \d+ < \d+$"):
        assert_valid_text_segment(seg)


def test_validator_rejects_offsets_out_of_range() -> None:
    """AI: Assert assert_valid_text_segment rejects a segment whose end_offset exceeds the full_text length."""
    seg = AutoTextSegment("abc", 0, 4)
    with pytest.raises(
        AssertionError,
        match=r"^Property end_offset out of range: \d+ not in \[0, \d+\]$",
    ):
        assert_valid_text_segment(seg)


def test_validator_rejects_inconsistent_text_segment_slice() -> None:
    """AI: Assert assert_valid_text_segment rejects a segment whose text_segment doesn't match the offset slice."""
    seg = InconsistentTextSlice("ab\ncd", 0, 2)
    with pytest.raises(
        AssertionError,
        match="text_segment and full_text\\[start_offset:end_offset\\] are inconsistent",
    ):
        assert_valid_text_segment(seg)


def test_validator_rejects_inconsistent_offset_and_line_column() -> None:
    """AI: Assert assert_valid_text_segment rejects a segment whose start offset doesn't match its (line, column)."""
    seg = InconsistentOffsets("ab\ncd", 0, 2)
    with pytest.raises(AssertionError, match="Start offset and \\(line, column\\) are inconsistent"):
        assert_valid_text_segment(seg)


def test_validator_rejects_line_out_of_range() -> None:
    """AI: Assert assert_valid_text_segment rejects a segment whose end_line precedes its start_line."""

    # Build a protocol-like object but with bogus line indices
    class BogusLine(AutoTextSegment):
        @property
        def start_line(self) -> int:
            return 999

    seg = BogusLine("ab\ncd", 0, 1)
    with pytest.raises(AssertionError, match=r"^Property end_line before start_line: \d+ < \d+$"):
        assert_valid_text_segment(seg)


def test_validator_rejects_column_out_of_range() -> None:
    """AI: Assert assert_valid_text_segment rejects a same-line segment whose end_column precedes its start_column."""

    class BogusColumn(AutoTextSegment):
        @property
        def start_column(self) -> int:
            return 999

    seg = BogusColumn("ab\ncd", 0, 1)
    with pytest.raises(
        AssertionError,
        match=r"^Property end_column before start_column, while start and end line are the same: \d+ < \d+$",
    ):
        assert_valid_text_segment(seg)


# -----------------------------
# Hypothesis strategies
# -----------------------------

# strategy to generate lines of text (with newline character)
text_line_strategy = st.text(
    alphabet=st.characters(exclude_categories=("Cs",), exclude_characters=["\n"]),
    min_size=0,
    max_size=25,
)

# strategy to generate text
# biased to contain multiple lines
# biased to end with \n
text_strategy = st.one_of(
    st.text(alphabet=st.characters(exclude_categories=("Cs",)), max_size=200),
    st.lists(text_line_strategy, min_size=1, max_size=20).map("\n".join),
    st.lists(text_line_strategy, min_size=1, max_size=20).map("\n".join).map(lambda s: s + "\n"),
)


# -----------------------------
# Property tests
# -----------------------------


@given(text=text_strategy)
def test_roundtrip_offset_loc_offset_for_all_cursor_offsets(text: str) -> None:
    """For all cursor offsets in [0, len(text)], converting offset -> (line, col) -> offset yields the original offset.

    This includes offset == len(text), which is essential for half-open ranges.
    """
    for offset in range(len(text) + 1):
        line, col = offset_to_location(text, offset)
        offset2 = location_to_offset(text, line, col)
        assert offset2 == offset


@given(text=text_strategy)
def test_offset_to_loc_corresponds_to_split_lines_extended_with_newlines(
    text: str,
) -> None:
    r"""For all cursor offsets in [0, len(text)], offset_to_loc matches the location computed from a canonical split of the text.

    parts = split(text, '\n')
        lines = parts[:-1] + '\n' + parts[-1]  (i.e., all but last extended with '\n')
    with canonical newline-boundary ownership:
        the cursor position after '\n' is (next_line, 0).
    """
    lines = split_lines_with_newlines(text)
    assert "".join(lines) == text  # sanity

    starts = line_starts_from_lines(lines)

    for offset in range(len(text) + 1):
        # Determine the (line, col) in the split-derived model.
        # Use bisect_right so that exact line starts map to that line (canonical).
        line = bisect.bisect_right(starts, offset) - 1
        col = offset - starts[line]

        # Canonicalization check:
        # If we're at the end boundary of a newline-terminated line (col == len(line_span)),
        # then the canonical representation should be (next_line, 0) (unless there is no next line).
        if line < len(lines) - 1 and lines[line].endswith("\n") and col == len(lines[line]):
            line += 1
            col = 0

        assert (line, col) == offset_to_location(text, offset)
