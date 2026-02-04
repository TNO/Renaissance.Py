import unittest

import pytest

import syntax_tree
from impl import PythonASTNode


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
        self.factory = syntax_tree.ASTFactory(PythonASTNode, [])

    def test_def_call_references(self):
        # Function f() refers to Function a()
        ast = self.factory.create_from_text(content2, 'content2.py')
        syntax_tree.ASTShower.store_node('c:/temp/py0.txt', ast)
        funcDef = syntax_tree.ASTFinder.find_kind(ast, 'FunctionDef').filter(lambda x: x.name == 'f').find_first().get()
        assert isinstance(funcDef, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = funcDef.references
        self.assertEqual(len(refs), 2)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        self.assertTrue(ref_node.name.lower(), 'a')
        referenced_by = ref_node.referenced_by
        self.assertEqual(len(referenced_by), 1)  # Function a referenced by function f and var x.
        self.assertTrue(funcDef in [r.node for r in referenced_by])
        ref1 = refs[1]
        ref_node1 = ref1.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        self.assertTrue(ref_node1.name.lower(), 'b')
        referenced_by1 = ref_node1.referenced_by
        self.assertEqual(len(referenced_by1), 1) # Function b referenced by function f.
        self.assertTrue(funcDef in [r.node for r in referenced_by])

    def test_type_reference(self):
        # Name z refers to Name a
        ast = self.factory.create_from_text('from abc import a\nx = a()\nz: a = x', 'content3.py')
        syntax_tree.ASTShower.store_node('c:/temp/py1.txt', ast)
        type_node = syntax_tree.ASTFinder.find_kind(ast, 'Name').filter(lambda x: x.name == 'z').find_first().get()
        assert isinstance(type_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = type_node.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'Name'), True)
        self.assertEqual(ref_node.name.lower(), 'a')
        referenced_by = ref_node.referenced_by
        self.assertGreater(len(referenced_by), 0)  # clang python returns 2 references, clang json 1
        self.assertTrue(type_node in [r.node for r in referenced_by])


    def test_class_reference(self):
        # Class A refers to Class B
        ast = self.factory.create_from_text(content3, 'content3.py')
        syntax_tree.ASTShower.store_node('c:/temp/py2.txt', ast)
        class_node = syntax_tree.ASTFinder.find_kind(ast, 'ClassDef').filter(lambda c: c.name == 'A').find_first().get()
        assert isinstance(class_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = class_node.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'ClassDef'), True)
        referenced_by = ref_node.referenced_by
        self.assertEqual(len(referenced_by), 2)
        self.assertTrue(class_node in [r.node for r in referenced_by])

    def test_param_reference(self):
        # param obj refers to its type, if type definition in the same file, refers to def, otherwise refers to Name
        ast = self.factory.create_from_text(content, 'content.py')
        syntax_tree.ASTShower.store_node('c:/temp/py3.txt', ast)
        param_node = syntax_tree.ASTFinder.find_kind(ast, 'arg').filter(lambda x: x.name.startswith('bruno')).find_first().get()
        assert isinstance(param_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = param_node.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'ClassDef'), True)
        referenced_by = ref_node.referenced_by
        self.assertEqual(len(referenced_by), 2)
        self.assertTrue(param_node in [r.node for r in referenced_by])

    def test_function_reference(self):
        ast = self.factory.create_from_text(content, 'content.py')
        syntax_tree.ASTShower.store_node('c:/temp/py3.txt', ast)
        call_node = syntax_tree.ASTFinder.find_kind(ast, 'Call').filter(lambda x: x.name.startswith('bruno.is_near')).find_first().get()
        assert isinstance(call_node, PythonASTNode)
        ast.translation_unit.lazy_create_refers(ast)
        refs = call_node.references
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(syntax_tree.ASTFinder.matches_kind(ref_node, 'FunctionDef'), True)
        referenced_by = ref_node.referenced_by
        self.assertEqual(len(referenced_by), 1)
        self.assertTrue(call_node in [r.node for r in referenced_by])

if __name__ == '__main__':
    unittest.main()
