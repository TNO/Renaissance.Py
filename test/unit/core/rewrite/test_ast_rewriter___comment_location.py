# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the ASTRewriter: locating the comment next to a code range."""

import pytest
from hamcrest import assert_that, is_

from renaissance.core.rewrite.ast_rewriter import _RewriteActions


class TestCommentLocation:
    """AI: Tests locating the trailing comment adjacent to a code range."""

    @pytest.mark.parametrize(
        ("_", "start_offset", "stop_offset", "content", "expected"),
        [
            (
                "single_line_comment",
                0,
                50,
                b"Some code // this is a comment\nMore code",
                (10, 30),
            ),
            (
                "double_line_comment",
                0,
                50,
                b"Some code// one\n // two\nMore code",
                (17, 23),
            ),
            (
                "block_comment",
                0,
                50,
                b"Some code /* this is a block comment */ More code",
                (10, 39),
            ),
            (
                "hash_comment",
                0,
                50,
                b"Some code # this is a hash comment\nMore code",
                (10, 34),
            ),
            ("no_comment", 0, 50, b"Some code with no comment\nMore code", (-1, -1)),
            (
                "comment_outside_range",
                0,
                10,
                b"Some code // this is a comment\nMore code",
                (-1, -1),
            ),
            (
                "multiple_comments",
                0,
                50,
                b"Some code // first comment\nMore code /* second comment */",
                (10, 26),
            ),
            pytest.param(
                "multiline_hash_comment",
                0,
                50,
                b"Some code\n# first\n# second\nMore code",
                (10, 26),
                marks=pytest.mark.xfail(
                    reason="get_comment_location only finds the single closest # line via rfind - "
                    "a multi-line contiguous comment block is truncated to its last line.",
                    strict=True,
                ),
            ),
            pytest.param(
                "multiline_slash_comment",
                0,
                50,
                b"Some code\n// first\n// second\nMore code",
                (10, 28),
                marks=pytest.mark.xfail(
                    reason="Same single-line limitation as multiline_hash_comment, for the // branch.",
                    strict=True,
                ),
            ),
        ],
    )
    def test(
        self,
        _,
        start_offset: int,
        stop_offset: int,
        content: bytes,
        expected: tuple[int, int],
    ) -> None:
        """Verify get_comment_location finds the expected comment span for each comment-style scenario."""
        result = _RewriteActions.get_comment_location(start_offset, stop_offset, content)
        assert_that(expected, is_(result))
