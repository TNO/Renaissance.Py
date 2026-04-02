# This script demonstrates the use of the syntax_tree library to parse and rewrite Python code.
# It specifically showcases nested replacements and multiple patterns.
import textwrap

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.impl.python.factory import PythonFactory
from renaissance.syntax_tree import ASTFactory, ASTRewriter
from renaissance.syntax_tree import ASTShower, TextUtils
from renaissance.syntax_tree.match_finder import match_pattern

example_code = """
from module import foo, bar, baz, quux
ba(51)
na(52)
na(53)
pa(54)
if pa():
  ba()
pa(54)  
"""


def python_ast_smoke_test():
    factory = PythonFactory(PythonASTNode)
    atu:PythonASTNode = PythonASTNode.load_from_text(example_code, "test.py")
    pattern_factory = PythonPatternFactory(
        factory,
    )

    pattern1 = pattern_factory.create_statements("if pa(): $$stmts")
    pattern2 = pattern_factory.create_expression("na($a)")

    ASTShower.show_node(pattern1, include_properties=True)

    pattern1replacement = textwrap.dedent("""
            # changed if expr to const
            isAOne=True
            if(isAOne):
                $$stmts
            """)
    pattern2replacement = "# changed function f1 to f2\nf2($a,123456)\n"

    rewriter = ASTRewriter(atu)
    for match in match_pattern(atu.body, pattern1):
        refactor(match, pattern1replacement, rewriter)
    for match in match_pattern(atu.body, [pattern2]):
        refactor(match, pattern2replacement, rewriter)
    return rewriter.apply_to_string()


def raw(nodes):
    res = ""
    for node in nodes:
        res += node.signature
    return res + "\n"


def refactor(match, replacement_text, rewriter):
    for repl_snippet in match.expansions:
        replacement_text = replacement_text.replace(repl_snippet, raw(match.expansions[repl_snippet]))
    return rewriter.replace(replacement_text, match.nodes)


if __name__ == "__main__":
    result = python_ast_smoke_test()
