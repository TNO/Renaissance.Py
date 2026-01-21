import ast
import unittest
from parameterized import parameterized
from impl import PythonASTNode, PythonPatternFactory, ClangASTNode
from impl.python import find_all
from syntax_tree import ASTFactory, MatchFinder, ASTShower, ASTFinder
import astpretty

def walk(node):
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(node.get_children())
        yield node

content = """
# antagonist
class cat:
    def __init__(self):
        self.out_of_shadow =True
    def is_near(self):
        return not self.out_of_shadow
# protagonist        
class mice:
    def be_high_alert_of(self):
        self.high_alert =True

    def discover(self, bruno:cat):
        if bruno.is_near():
            self.be_high_alert_of()
# main function
if __name__ == '__main__':
    jerry = mice()
    tom = cat()
    jerry.discover(tom)

""".strip()

class PythonNodeTest(unittest.TestCase):
    def test_reference_nodes(self):
        self.factory = ASTFactory(PythonASTNode, [])
        tree = self.factory.create_from_text(content, 'all.py')
        tree.translation_unit.lazy_create_references(tree)
        self.assertIn('cat.__init__',tree.translation_unit.references,'detects functions')
        self.assertIn('mice.discover[bruno]',tree.translation_unit.references,'detects parameters')
        self.assertIn('tom', tree.translation_unit.references, 'detects global')
if __name__ == '__main__':
    unittest.main()
