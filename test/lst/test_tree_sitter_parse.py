import pytest
from hamcrest import assert_that, is_
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava

# Load compiled languages
PY_LANGUAGE = Language(tspython.language())
CPP_LANGUAGE = Language(tscpp.language())
JAVA_LANGUAGE = Language(tsjava.language())

# Create parsers
py_parser = Parser(PY_LANGUAGE)
cpp_parser = Parser(CPP_LANGUAGE)
java_parser = Parser(JAVA_LANGUAGE)

# Sample inputs
py_code = b'def foo():\n    if bar:\n        baz()\n'

cpp_code = (b'public class Test {\n    public static void main(String[] args) {\n       '
 b' if (ready) start();\n    }\n}\n')

java_code = (b'public class Test {\n    public static void main(String[] args) {\n       '
 b' if (ready) start();\n    }\n}\n')
class TestTreeSitterParse:
    def test_parse_py_code(self):
        assert_that(py_code, is_(py_parser.parse(py_code).root_node.text))


    def test_parse_cpp_code(self):
        assert_that(cpp_code, is_(cpp_parser.parse(cpp_code).root_node.text))


    def test_parse_java_code(self):
        assert_that(java_code, is_(java_parser.parse(java_code).root_node.text))



