import tree_sitter_python as tspython

from renaissance.impl.python import PythonPatternFactory
from renaissance.impl.tree_sitter_adapter import TreeSitterAdapter, TsPatternFactory
from renaissance.lst.lst import LSTNode
from renaissance.syntax_tree import MatchFinder, ASTShower, ASTFinder, ASTFactory, ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern

code = """
def greet(name):
    print("Hello", name)

if True:
    greet("World")
"""
adapter = TreeSitterAdapter(tspython)
tree = adapter.parse_code(code)
lst = adapter.to_lst(code, tree)

# Show the root of the LST
ASTShower.show_node(lst.root)


nodes=ASTFinder.find_kind(lst.root, "identifier").to_list()

ASTShower.show_node(nodes[0])

pattern_factory = TsPatternFactory(adapter)

pattern = pattern_factory.create_statements("$greet($arg)")

matches=match_pattern(lst.root.children, pattern)

ASTShower.show_node(matches[0].nodes[0])
rewriter = ASTRewriter(lst.root)


def raw(nodes):
    res = ''
    for node in nodes:
        res += node.signature
    return res + '\n'

for match in matches:
    replment_text = "my_awesome_$greet($arg,'is','awesome)"
    for repl_snippet in match.expansions:
        replment_text = replment_text.replace(repl_snippet, raw(match.expansions[repl_snippet]))
    rewriter.replace(replment_text, match.nodes)
result = rewriter.apply_to_string()
print(result)
# if rewriter.has_changed():
#     atu = factory.create_from_text(result, 'test.py')
# else:
#     atu = None
