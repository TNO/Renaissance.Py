from adapters.tree_sitter_adapter import TreeSitterAdapter
import tree_sitter_python as tspython

from syntax_tree import MatchFinder, ASTShower


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
