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
def test_parse_py_code():
    assert py_code == py_parser.parse(py_code).root_node.text


def test_parse_cpp_code():
    assert cpp_code == cpp_parser.parse(cpp_code).root_node.text


def test_parse_java_code():
    assert java_code ==  java_parser.parse(java_code).root_node.text
