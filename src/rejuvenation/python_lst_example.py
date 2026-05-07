import textwrap

import tree_sitter_python

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.tree_sitter.lst import LST, LSTNode
from renaissance.impl import MATCH_ONE
from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter.factory import TreeStiterPatternFactory

from renaissance.syntax_tree import ASTShower, ASTRewriter
from renaissance.syntax_tree.ast_finder import find_kind
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


def python_lst_smoke_test():

    # adapter = TreeSitterAdapter(tree_sitter_python)
    # tree = adapter.parse_code(code)
    # lst = adapter.to_lst(code, tree)

    factory = PythonFactory(LSTNode)
    pattern_factory = PythonPatternFactory(factory)

    atu = factory.create_from_text(example_code, "example.py")

    pattern1 = pattern_factory.create_statement("if pa(): $$stmts")
    pattern2 = pattern_factory.create_expression("na($a)")

    print("_______________pattern 1____________________________________")
    ASTShower.show_node(pattern1.node, include_properties=True)
    print("_______________pattern 1____________________________________")
    ASTShower.show_node(pattern2.node, include_properties=False)
    print("_______________ast____________________________________")
    ASTShower.focus = "ba"
    ASTShower.show_node(atu)

    print("_______________simple find____________________________________")
    nodes = find_kind(atu, "Call")

    ASTShower.show_node(nodes[0])

    pattern1replacement = textwrap.dedent("""
            # changed if expr to const
            isAOne=True
            if(isAOne):
                $$stmts
            """)
    pattern2replacement = "# changed function f1 to f2\nf2($a,123456)\n"

    rewriter = ASTRewriter(atu)

    for match in match_pattern(atu.children, [pattern1]):
        refactor(match, pattern1replacement, rewriter)

    for match in match_pattern(atu.children, [pattern2]):
        refactor(match, pattern2replacement, rewriter)

    return rewriter.apply_to_string()


def refactor(match, replacement_text, rewriter):
    for placeholder in match.expansions:
        replacement_text = replacement_text.replace(placeholder, match[placeholder])
    return rewriter.replace(replacement_text, match.nodes)


if __name__ == "__main__":
    result = python_lst_smoke_test()
    print("_______________end result_________________________________")
    print(result)
