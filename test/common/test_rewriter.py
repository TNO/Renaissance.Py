import pytest
from hamcrest import *

from renaissance.common.rewriter import Rewriter


class TestRewriter:

    @pytest.mark.parametrize("initial_bytes, start, end, new_content, expected_bytes",[
        (b'abcdefghij', 5, 10, b"hellooo", b'abcdehellooo'),
        (b'abcdefghij', 5, 10, b" world", b'abcde world'),
        (b'abcdefghij', 0, 0, b"BEGIN", b'BEGINabcdefghij'),
        (b'abcdefghij', 2, 4, b"XY", b'abXYefghij'),
        (b'abcdefghij', 0, 10, b"REPLACED", b'REPLACED'),
        (b'abcdefghij', -1, -1, b"AT_END", b'abcdefghijAT_END'),
        (b'abcdefghij', 5, -1, b"AT_END", b'abcdeAT_END'),
    ])
    def test_replace(self, initial_bytes, start, end, new_content, expected_bytes):
        rewriter = Rewriter(initial_bytes)
        rewriter.replace(start, end, new_content)
        result = rewriter.apply()
        assert_that(expected_bytes, is_(result))

    def test_multiple_replaces(self):
        initial_bytes = b'abcdefghij'
        rewriter = Rewriter(initial_bytes)
        rewriter.replace(5, 10, b"hello")
        rewriter.replace(5, 10, b" world")
        rewriter.replace(0, 0, b"BEGIN")
        result = rewriter.apply()
        assert_that(result, is_(b'BEGINabcdehello world'))
