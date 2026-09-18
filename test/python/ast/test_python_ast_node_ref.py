"""Tests for Python RST AST node references."""

import tempfile

import pytest
from hamcrest import assert_that, greater_than, has_length, has_string, is_, is_in
from more_itertools.more import first

from renaissance import syntax_tree
from renaissance.integrations.python.ast.factory import PythonFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode, PythonRSTReference
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import traverse

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
    """AI: Tests resolving references between Python AST nodes (function calls, definitions)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up fixture state before each test method."""
        self.factory = PythonFactory(PythonRstNode)

    def test_def_call_references(self):
        """AI: Verify function f's references to functions a and b are resolved, each referenced back by f."""
        # Function f() refers to Function a()
        ast = PythonRstNode.load_from_text(content2)
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py0.txt", ast)

        func_def = first(n for n in traverse(ast) if n.semantic_kind is SemanticKind.FUNCTION and n.name == "f")
        assert_that(func_def, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = func_def.references
        assert_that(refs, has_length(2))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.semantic_kind is SemanticKind.FUNCTION, is_(True))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))  # Function a referenced by function f and var x.
        assert_that(func_def in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])
        ref1 = refs[1]
        ref_node1 = ast.translation_unit._nodes[ref1.node_id]
        assert_that(ref_node1.semantic_kind is SemanticKind.FUNCTION, is_(True))
        assert_that(ref_node1.name.lower(), is_("b"))
        referenced_by1 = ref_node1.referenced_by
        assert_that(referenced_by1, has_length(1))  # Function b referenced by function f.
        assert_that(func_def in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_type_reference(self):
        """AI: Verify a type-annotated name resolves its reference to the imported name it annotates."""
        # Name z refers to Name a
        ast = self.factory.create_from_text("from abc import a\nx = a()\nz: a = x", "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py1.txt", ast)
        type_node = first(n for n in traverse(ast) if n.semantic_kind is SemanticKind.NAME and n.name == "z")
        assert_that(type_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = type_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.semantic_kind is SemanticKind.NAME, is_(True))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))
        assert_that(type_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_class_reference(self):
        """AI: Verify a subclass resolves its reference to its base class."""
        # Class A refers to Class B
        ast = self.factory.create_from_text(content3, "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py2.txt", ast)

        class_node = first(n for n in traverse(ast) if n.semantic_kind is SemanticKind.CLASS and n.name == "A")

        assert_that(class_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = class_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.semantic_kind is SemanticKind.CLASS, is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        assert_that(class_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_param_reference(self):
        """AI: Verify a parameter's type annotation resolves its reference to the class defined in the same file."""
        # param obj refers to its type, if type definition in the same file, refers to def, otherwise refers to Name
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py3.txt", ast)

        param_node = [n for n in traverse(ast) if n.name == "bruno" and n.parser_kind == "arg"]

        assert_that(param_node[0], is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = param_node[0].references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.semantic_kind is SemanticKind.CLASS, is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        types = [r.node_id for r in referenced_by]
        assert_that(param_node[0].name, is_in(types))

    def test_function_reference(self):
        """AI: Verify a method call resolves its reference to the method it calls."""
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py4.txt", ast)
        call_node = first(n for n in traverse(ast) if n.semantic_kind is SemanticKind.CALL and n.name == "bruno.is_near()")
        assert_that(call_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = call_node.references
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]

        assert_that(ref_node.semantic_kind is SemanticKind.FUNCTION, is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))
        assert_that(call_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_ref_node_to_str(self):
        """AI: Verify PythonRSTReference's string representation combines its message and kind."""
        it = PythonRSTReference("it is ", "kind", {})
        assert_that(it, has_string("it is :kind"))

    @pytest.mark.parametrize("def_keyword", ["def", "async def"])
    def test_return_type_reference(self, def_keyword):
        """AI: Verify a function's return type annotation resolves its reference to the annotated class."""
        # Function make_config()'s return annotation refers to Class Config.
        code = f"class Config:\n    pass\n\n{def_keyword} make_config() -> Config:\n    pass\n"
        ast = self.factory.create_from_text(code, "content.py")
        func_node = first(n for n in traverse(ast) if n.name == "make_config")
        ast.translation_unit.lazy_create_refers(ast)
        refs = func_node.references
        assert_that(refs, has_length(1))
        ref_node = ast.translation_unit._nodes[refs[0].node_id]
        assert_that(ref_node.semantic_kind is SemanticKind.CLASS, is_(True))

    def test_function_without_return_annotation_has_no_type_reference(self):
        """AI: Verify a function without a return annotation has no references."""
        ast = self.factory.create_from_text("def f():\n    pass\n", "content.py")
        func_node = first(n for n in traverse(ast) if n.name == "f")
        ast.translation_unit.lazy_create_refers(ast)
        assert_that(func_node.references, has_length(0))


if __name__ == "__main__":
    pytest.main()
