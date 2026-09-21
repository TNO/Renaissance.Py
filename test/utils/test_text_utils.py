"""Tests for the snake_case text utility."""

import pytest
from hamcrest import assert_that, is_

from renaissance.utils.text_utils import snake_case


class TestSnakeCase:
    """AI: Tests for the snake_case text utility."""

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("A", "a"),
            ("already_snake", "already_snake"),
            ("Base64Encode", "base64_encode"),
            ("CamelCase", "camel_case"),
            ("HTML5Parser", "html5_parser"),
            ("HTMLParser", "html_parser"),
            ("Python3Refactoring", "python3_refactoring"),
            ("PythonRefactoring", "python_refactoring"),
            ("SimplifyRenaissance", "simplify_renaissance"),
            ("TestSnakeCase", "test_snake_case"),
        ],
    )
    def test_snake_case(self, input_str, expected):
        """AI: Assert snake_case converts camelCase/PascalCase strings to snake_case, preserving acronyms."""
        assert_that(snake_case(input_str), is_(expected))
