import ast
import unittest

import pytest
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
        todo.extend(node.children)
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

content2 = """
def a() -> int:
    return 42
def b(x) -> None:
    x += 1
def f() -> None:
    x: int = a()
    b(x)
    # do something with x
""".strip()

content3 = """
class B:
    def __init__(self, value):
        self.value = value
    def base_method(self):
        return "This method is defined in the base class B"

class A(B):
    def __init__(self, value, extra_value):
        # Call the parent class's __init__ method
        super().__init__(value)
        self.extra_value = extra_value
    def subclass_method(self):
        return "This method is only in subclass A"
        
# Create instances of both classes
b_instance = B("Base")
a_instance = A("Derived", "Extra")
"""

class PythonNodeTest(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup that runs before each test method"""
        self.factory = ASTFactory(PythonASTNode, [])


    def test_reference_nodes(self):
        tree = self.factory.create_from_text(content, 'all.py')
        tree.translation_unit.lazy_create_references(tree)
        self.assertIn('cat.__init__', tree.translation_unit._references,'detects functions')
        self.assertIn('mice.discover[bruno]', tree.translation_unit._references,'detects parameters')
        self.assertIn('tom', tree.translation_unit._references, 'detects global')
        self.assertIn('mice.be_high_alert_of', tree.translation_unit._references, 'detects functions')

    def test_def_call_references(self):
        # Function f() refers to Function a()
        ast = self.factory.create_from_text(content2, 'content2.py')
        ASTShower.store_node('c:/temp/py0.txt', ast)
        funcDef = ASTFinder.find_kind(ast, 'FunctionDef').filter(lambda x: x.get_name() == 'f').find_first().get()
        assert isinstance(funcDef, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = funcDef.get_references()
        self.assertEqual(len(refs), 2)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        self.assertTrue(ref_node.get_name().lower(), 'a')
        referenced_by = ref_node.get_referenced_by()
        self.assertEqual(len(referenced_by), 1)  # Function a referenced by function f and var x.
        self.assertTrue(funcDef in [r.get_node() for r in referenced_by])
        ref1 = refs[1]
        ref_node1 = ref1.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        self.assertTrue(ref_node1.get_name().lower(), 'b')
        referenced_by1 = ref_node1.get_referenced_by()
        self.assertEqual(len(referenced_by1), 1) # Function b referenced by function f.
        self.assertTrue(funcDef in [r.get_node() for r in referenced_by])

    def test_type_reference(self):
        # Name z refers to Name a
        ast = self.factory.create_from_text('from abc import a\nx = a()\nz: a = x', 'content3.py')
        ASTShower.store_node('c:/temp/py1.txt', ast)
        type_node = ASTFinder.find_kind(ast, 'Name').filter(lambda x: x.get_name() == 'z').find_first().get()
        assert isinstance(type_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = type_node.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'Name'), True)
        self.assertEqual(ref_node.get_name().lower(), 'a')
        referenced_by = ref_node.get_referenced_by()
        self.assertGreater(len(referenced_by), 0)  # clang python returns 2 references, clang json 1
        self.assertTrue(type_node in [r.get_node() for r in referenced_by])


    def test_class_reference(self):
        # Class A refers to Class B
        ast = self.factory.create_from_text(content3, 'content3.py')
        ASTShower.store_node('c:/temp/py2.txt', ast)
        class_node = ASTFinder.find_kind(ast, 'ClassDef').filter(lambda c: c.get_name() == 'A').find_first().get()
        assert isinstance(class_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = class_node.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'ClassDef'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertEqual(len(referenced_by), 2)
        self.assertTrue(class_node in [r.get_node() for r in referenced_by])

    def test_param_reference(self):
        # param obj refers to its type, if type definition in the same file, refers to def, otherwise refers to Name
        ast = self.factory.create_from_text(content, 'content.py')
        ASTShower.store_node('c:/temp/py3.txt', ast)
        param_node = ASTFinder.find_kind(ast, 'arg').filter(lambda x: x.get_name().startswith('bruno')).find_first().get()
        assert isinstance(param_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = param_node.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'ClassDef'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertEqual(len(referenced_by), 2)
        self.assertTrue(param_node in [r.get_node() for r in referenced_by])

    def test_function_reference(self):
        ast = self.factory.create_from_text(content, 'content.py')
        ASTShower.store_node('c:/temp/py3.txt', ast)
        call_node = ASTFinder.find_kind(ast, 'Call').filter(lambda x: x.get_name().startswith('bruno.is_near')).find_first().get()
        assert isinstance(call_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = call_node.get_references()
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertEqual(len(referenced_by), 1)
        self.assertTrue(call_node in [r.get_node() for r in referenced_by])



if __name__ == '__main__':
    unittest.main()
