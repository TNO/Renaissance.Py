from adapters.tree_sitter_adapter import TreeSitterAdapter
import tree_sitter_python as tspython

from syntax_tree import MatchFinder

code = """
def greet(name):
    print("Hello", name)

if True:
    greet("World")
"""
print(code)
adapter = TreeSitterAdapter(tspython)
tree = adapter.parse_code(code)
lst = adapter.to_lst(code, tree)
for node in lst.traverse():
    print(node)
#
# self.assertIsInstance(lst, LST)
# nodes = list(lst.traverse())
#
# for node in lst.traverse():
#     print(node)
