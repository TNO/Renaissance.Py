import tempfile

import pytest
from hamcrest import *

from renaissance import syntax_tree
from renaissance.impl.python import PythonASTNode
from renaissance.impl.python.python_ast_node import PythonASTReference
from renaissance.syntax_tree import ASTNode

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


class TestPythonNode:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup that runs before each test method"""
        self.factory = syntax_tree.ASTFactory(PythonASTNode, [])

    def test_def_call_references(self):
        # Function f() refers to Function a()
        ast = PythonASTNode.load_from_text(content2, "content2.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py0.txt", ast)

        func_def = syntax_tree.ASTFinder.find_kind(ast, "FunctionDef").filter(lambda x: x.name == "f").find_first().get()
        assert_that(func_def, is_(PythonASTNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = func_def.references
        assert_that(refs, has_length(2))
        ref = refs[0]
        ref_node: ASTNode = ref.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "FunctionDef"), is_(True))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))  # Function a referenced by function f and var x.
        assert_that(func_def in [r.node for r in referenced_by])
        ref1 = refs[1]
        ref_node1 = ref1.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "FunctionDef"), is_(True))
        assert_that(ref_node1.name.lower(), is_("b"))
        referenced_by1 = ref_node1.referenced_by
        assert_that(referenced_by1, has_length(1))  # Function b referenced by function f.
        assert_that(func_def in [r.node for r in referenced_by])

    def test_type_reference(self):
        # Name z refers to Name a
        ast = self.factory.create_from_text("from abc import a\nx = a()\nz: a = x", "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py1.txt", ast)

        type_node = syntax_tree.ASTFinder.find_kind(ast, "Name").filter(lambda x: x.name == "z").find_first().get()
        assert_that(type_node, is_(PythonASTNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = type_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ref.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "Name"), is_(True))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))
        assert_that(type_node in [r.node for r in referenced_by])

    def test_class_reference(self):
        # Class A refers to Class B
        ast = self.factory.create_from_text(content3, "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py2.txt", ast)
        class_node = syntax_tree.ASTFinder.find_kind(ast, "ClassDef").filter(lambda c: c.name == "A").find_first().get()
        assert_that(class_node, is_(PythonASTNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = class_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ref.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "ClassDef"), is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        assert_that(class_node in [r.node for r in referenced_by])

    def test_param_reference(self):
        # param obj refers to its type, if type definition in the same file, refers to def, otherwise refers to Name
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py3.txt", ast)

        param_node = syntax_tree.ASTFinder.find_kind(ast, "arg").filter(lambda x: x.name.startswith("bruno")).find_first().get()
        assert_that(param_node, is_(PythonASTNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = param_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ref.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "ClassDef"), is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        assert_that(param_node in [r.node for r in referenced_by])

    def test_function_reference(self):
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py4.txt", ast)
        call_node = syntax_tree.ASTFinder.find_kind(ast, "Call").filter(lambda x: x.name.startswith("bruno.is_near")).find_first().get()
        assert_that(call_node, is_(PythonASTNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = call_node.references
        ref = refs[0]
        ref_node = ref.node
        assert_that(syntax_tree.ASTFinder.matches_kind(ref_node, "FunctionDef"), is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))
        assert_that(call_node in [r.node for r in referenced_by])


def test_ref_node_to_str():
    it = PythonASTReference("it is ", "kind", {})
    assert_that(it, has_string("it is :kind"))


if __name__ == "__main__":
    pytest.main()
