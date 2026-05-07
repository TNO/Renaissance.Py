from renaissance.syntax_tree.text_segment import TextSegment


def offset_to_location(text: str, offset: int) -> tuple[int, int]:
    """
    Convert a *cursor offset* (0 <= offset <= len(text)) to canonical (line, column),
    both 0-based.

    Canonical rule:
    - The position immediately after a '\n' belongs to the next line at column 0.
      (So offset k where k>0 and text[k-1] == '\n' maps to (line_of_next, 0).)

    Newline character itself is on the terminating line at its own column.
    """
    assert 0 <= offset <= len(text)

    line = 0
    line_start = 0

    # Scan characters strictly before this cursor position.
    # When we pass a '\n', we move to the next line whose start is i+1.
    for i, ch in enumerate(text):
        if i >= offset:
            break
        if ch == "\n":
            line += 1
            line_start = i + 1

    col = offset - line_start
    return line, col


def location_to_offset(text: str, line: int, column: int) -> int:
    """
    Convert canonical (line, column) back to a cursor offset, validating that the
    (line, column) is a valid cursor position under canonical rules.

    Valid cursor columns:
    - For an empty line (span_len==0): only column==0.
    - For a non-empty line:
        * If it ends with '\n': allowed columns are 0..span_len-1 (cursor after '\n' is canonicalized to next line).
        * Else: allowed columns are 0..span_len (end-of-text / end-of-line cursor position).
    """
    lines = split_lines_with_newlines(text)
    starts = line_starts_from_lines(lines)

    assert 0 <= line < len(lines)
    span = lines[line]
    span_len = len(span)

    if span_len == 0:
        assert column == 0
        return starts[line]

    ends_with_nl = span[-1] == "\n"
    if ends_with_nl:
        # canonical: disallow column == span_len (cursor after '\n')
        assert 0 <= column < span_len
    else:
        # last line (or any non-nl-terminated line): allow cursor at end boundary
        assert 0 <= column <= span_len

    return starts[line] + column


def assert_valid_text_segment(text_segment: TextSegment) -> None:
    assert isinstance(text_segment, TextSegment), f"Unexpected instance for text_segment '{type(text_segment)}'. Expected 'TextSegment'."
    assert isinstance(
        text_segment.full_text, str
    ), f"Unexpected instance for property full_text '{type(text_segment.full_text)}'. Expected 'str'."
    assert isinstance(
        text_segment.text_segment, str
    ), f"Unexpected instance for property text_segment '{type(text_segment.text_segment)}'. Expected 'str'."
    # TODO: should we check the types of all properties?

    # offset
    assert (
        text_segment.start_offset <= text_segment.end_offset
    ), f"Property end_offset before start_offset: {text_segment.end_offset} < {text_segment.start_offset}"

    ## allow pointing at end-of-text position
    length_full_text = len(text_segment.full_text)
    assert (
        0 <= text_segment.start_offset <= length_full_text
    ), f"Property start_offset out of range: {text_segment.start_offset} not in [0, {length_full_text}]"
    assert (
        0 <= text_segment.end_offset <= length_full_text
    ), f"Property end_offset out of range: {text_segment.end_offset} not in [0, {length_full_text}]"

    # line column pair
    ## TODO: Is this a better alternative than using tuple comparison (start_line, end_line) <= (end_line, end_column)?
    assert (
        text_segment.start_line <= text_segment.end_line
    ), f"Property end_line before start_line: {text_segment.end_line} < {text_segment.start_line}"
    assert not (text_segment.start_line == text_segment.end_line) or text_segment.start_column <= text_segment.end_column, (
        "Property end_column before start_column, while start and end line are the same: "
        + f"{text_segment.end_column} < {text_segment.start_column}"
    )

    line_starts = _compute_line_starts(text_segment.full_text)

    ## line range
    lines = len(line_starts)
    assert 0 <= text_segment.start_line < lines, f"Property start_line out of range: {text_segment.start_line} not in [0, {lines})"
    assert 0 <= text_segment.end_line < lines, f"Property end_line out of range: {text_segment.end_line} not in [0, {lines})"

    ## column range
    _check_column_range(
        len(text_segment.full_text),
        text_segment.start_line,
        text_segment.start_column,
        line_starts,
        "start_column",
    )
    _check_column_range(
        len(text_segment.full_text),
        text_segment.end_line,
        text_segment.end_column,
        line_starts,
        "end_column",
    )

    # consistency offset and line column pair
    assert (
        text_segment.start_offset == line_starts[text_segment.start_line] + text_segment.start_column
    ), "Start offset and (line, column) are inconsistent"
    assert (
        text_segment.end_offset == line_starts[text_segment.end_line] + text_segment.end_column
    ), "End offset and (line, column) are inconsistent"

    # consistency full_text and text_segment
    assert (
        text_segment.text_segment == text_segment.full_text[text_segment.start_offset : text_segment.end_offset]
    ), "text_segment and full_text[start_offset:end_offset] are inconsistent"


def _check_column_range(
    length_full_text: int,
    line: int,
    column: int,
    line_starts: tuple[int, ...],
    description: str,
):
    start_line = line_starts[line]
    end_line = (
        length_full_text + 1  ## column must be able to point beyond last character of full text to include that character as well.
        if line + 1 == len(line_starts)
        else line_starts[line + 1]
    )
    length_line = end_line - start_line
    assert 0 <= column < length_line, f"Property {description} out of range: {column} not in [0, {length_line})"


def split_lines_with_newlines(text: str) -> list[str]:
    """
    Reference 'lines' derived from split(text, '\n') with all but last extended by '\n'.
    This yields a list where each element corresponds to the characters of that line span,
    and all '\n' characters belong to the line they terminate.
    """
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def line_starts_from_lines(lines: list[str]) -> list[int]:
    """
    Compute the starting cursor offsets for each line from the line-span strings.
    """
    starts = [0]
    acc = 0
    for s in lines[:-1]:
        acc += len(s)
        starts.append(acc)
    return starts


def _compute_line_starts(text: str) -> tuple[int, ...]:
    """
    Return a tuple with the offset of the first character of that line.
    The offset is 0 based. The first line will always starts at offset 0.
    """
    line_starts: list[int] = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)  # next line starts after '\n' (0-based offset)
    return tuple(line_starts)
