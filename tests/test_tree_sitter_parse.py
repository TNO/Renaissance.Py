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
py_code = b"""
def foo():
    if bar:
        baz()
"""

cpp_code = b"""
int main() {
    if (flag) run();
}
"""

java_code = b"""
public class Test {
    public static void main(String[] args) {
        if (ready) start();
    }
}
"""

# Parse and print root nodes
print("Python:\n", py_parser.parse(py_code).root_node.text)
print("\nC++:\n", cpp_parser.parse(cpp_code).root_node.text)
print("\nJava:\n", java_parser.parse(java_code).root_node.text)
