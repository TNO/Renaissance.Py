from adapters.tree_sitter_adapter import TreeSitterAdapter
import tree_sitter_python as tspython

from renaissance.impl import PythonPatternFactory
from renaissance.lst.lst import LSTNode
from renaissance.syntax_tree import MatchFinder, ASTShower, ASTFinder, ASTFactory

code = """
def greet(name):
    print("Hello", name)

if True:
    greet("World")
"""
adapter = TreeSitterAdapter(tspython)
tree = adapter.parse_code(code)
lst = adapter.to_lst(code, tree)
ASTShower.show_node(lst.root)

nodes=ASTFinder.find_kind(lst.root, "identifier").to_list()

ASTShower.show_node(nodes[0])
factory = ASTFactory(LSTNode)
pattern_factory = PythonPatternFactory(factory,lst)
pattern = pattern_factory.create_statements("$greet($arg)")
nodes=MatchFinder.find_kind(lst.root, pattern).to_list()

ASTShower.show_node(nodes[0])

