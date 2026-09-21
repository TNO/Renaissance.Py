"""Tests raw tree-sitter parsing across multiple language grammars."""

import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from hamcrest import assert_that, is_

from tree_sitter import Language, Parser

# Load compiled languages
PY_LANGUAGE = Language(tspython.language())
CPP_LANGUAGE = Language(tscpp.language())
JAVA_LANGUAGE = Language(tsjava.language())

# Create parsers
py_parser = Parser(PY_LANGUAGE)
cpp_parser = Parser(CPP_LANGUAGE)
java_parser = Parser(JAVA_LANGUAGE)

# Sample inputs
py_code = b"def foo():\n    if bar:\n        baz()\n"

cpp_code = b"public class Test {\n    public static void main(String[] args) {\n        if (ready) start();\n    }\n}\n"

java_code = b"public class Test {\n    public static void main(String[] args) {\n        if (ready) start();\n    }\n}\n"


class TestTreeSitterParse:
    """AI: Tests raw tree-sitter parsing across multiple language grammars."""

    def test_parse_py_code(self):
        """AI: Verify raw tree-sitter parsing of Python source round-trips through root_node.text."""
        assert_that(py_code, is_(py_parser.parse(py_code).root_node.text))

    def test_parse_cpp_code(self):
        """AI: Verify raw tree-sitter parsing of C++ source round-trips through root_node.text."""
        assert_that(cpp_code, is_(cpp_parser.parse(cpp_code).root_node.text))

    def test_parse_java_code(self):
        """AI: Verify raw tree-sitter parsing of Java source round-trips through root_node.text."""
        assert_that(java_code, is_(java_parser.parse(java_code).root_node.text))
