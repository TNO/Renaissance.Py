import pytest
from hamcrest import assert_that, is_

from renaissance.utils.text_utils import camel_case, snake_case


class TestSnakeCase:
    @pytest.mark.parametrize("input_str, expected", [
        ("CamelCase", "camel_case"),
        ("Unit2Pytest", "unit2pytest"),
        ("SimplifyRenaissance", "simplify_renaissance"),
        ("PythonRefactoring", "python_refactoring"),
        ("already_snake", "already_snake"),
        ("A", "a"),
        ("HTMLParser", "html_parser"),
    ])
    def test_snake_case(self, input_str, expected):
        assert_that(snake_case(input_str), is_(expected))


class TestCamelCase:
    @pytest.mark.parametrize("input_str, expected", [
        ("camel_case", "camelCase"),
        ("simplify_renaissance", "simplifyRenaissance"),
        ("python_refactoring", "pythonRefactoring"),
        ("already_snake", "alreadySnake"),
        ("a", "a"),
        ("html_parser", "htmlParser"),
    ])
    def test_camel_case(self, input_str, expected):
        assert_that(camel_case(input_str), is_(expected))


