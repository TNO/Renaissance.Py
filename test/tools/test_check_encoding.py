# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the encoding guard rail in tools/check_encoding.py.

The tests run against byte strings and temporary files, so they do not depend on the contents of the repository.
"""

from pathlib import Path

from tools import check_encoding


def test_ascii_is_accepted() -> None:
    """Assert a plain ASCII file passes, since ASCII is a subset of UTF-8."""
    assert check_encoding.encoding_problem(b"print('hello')\n") is None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_utf_8_without_a_byte_order_mark_is_accepted() -> None:
    """Assert non-ASCII characters encoded as UTF-8 pass."""
    assert check_encoding.encoding_problem("ligné ⚠".encode()) is None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_latin_1_is_reported() -> None:
    """Assert a byte that cannot start a UTF-8 sequence is reported with its offset."""
    problem = check_encoding.encoding_problem("ligné".encode("latin-1"))
    assert problem is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert "offset 4" in problem  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_utf_8_byte_order_mark_is_reported() -> None:
    """Assert a UTF-8 byte order mark is reported, even though the file decodes as UTF-8."""
    problem = check_encoding.encoding_problem("\ufeffprint('hello')\n".encode())
    assert problem == "starts with a UTF-8 byte order mark"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_utf_16_is_reported_as_a_byte_order_mark_rather_than_as_binary() -> None:
    """Assert UTF-16 text is reported, although its NUL bytes would otherwise make it look binary."""
    problem = check_encoding.encoding_problem("print('hello')\n".encode("utf-16"))
    assert problem is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert "UTF-16" in problem  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_binary_content_is_skipped() -> None:
    """Assert a file without an encoding, such as an image, is not judged."""
    assert check_encoding.encoding_problem(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe") is None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_nul_byte_after_the_sniffed_block_does_not_hide_a_broken_file() -> None:
    """Assert the binary heuristic only looks at the first block, as git does."""
    problem = check_encoding.encoding_problem(b"a" * check_encoding.BINARY_SNIFF_BYTES + b"\xe9\x00")
    assert problem is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert "not valid UTF-8" in problem  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_find_violations_names_only_the_offending_file(tmp_path: Path) -> None:
    """Assert the violations are the offending files, described relative to the root."""
    (tmp_path / "good.py").write_bytes("ligné".encode())
    (tmp_path / "bad.py").write_bytes("ligné".encode("latin-1"))
    violations = check_encoding.find_violations(tmp_path.iterdir())
    assert [violation.describe(tmp_path).split(":")[0] for violation in violations] == ["bad.py"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_tracked_path_that_is_absent_from_the_working_tree_is_skipped(tmp_path: Path) -> None:
    """Assert a path that does not exist, as during a sparse checkout, does not fail the check."""
    assert check_encoding.find_violations([tmp_path / "gone.py"]) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
