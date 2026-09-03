import tempfile

import pytest
from hamcrest import assert_that, empty, greater_than, has_length, has_string, instance_of, is_, is_in
from more_itertools.more import first

from renaissance import syntax_tree
from renaissance.impl.python.factory import PythonFactory
from renaissance.impl.python.rst_node import PythonRstNode, PythonRSTReference
from renaissance.impl.types import Arg, Call, ClassDef, FunctionDef, Name
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


returning_content = """
class Cat:
    pass

def find() -> Cat:
    return None
""".strip()


class TestPythonNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup that runs before each test method."""
        self.factory = PythonFactory(PythonRstNode)

    def test_def_call_references(self):
        # Function f() refers to Function a()
        ast = PythonRstNode.load_from_text(content2)
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py0.txt", ast)

        func_def = first(n for n in traverse(ast) if isinstance(n.ast_type(), FunctionDef) and n.name == "f")
        assert_that(func_def, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = func_def.references
        assert_that(refs, has_length(2))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.ast_type(), instance_of(FunctionDef))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))  # Function a referenced by function f and var x.
        assert_that(func_def in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])
        ref1 = refs[1]
        ref_node1 = ast.translation_unit._nodes[ref1.node_id]
        assert_that(ref_node.ast_type(), instance_of(FunctionDef))
        assert_that(ref_node1.name.lower(), is_("b"))
        referenced_by1 = ref_node1.referenced_by
        assert_that(referenced_by1, has_length(1))  # Function b referenced by function f.
        assert_that(func_def in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_type_reference(self):
        # Name z refers to Name a
        ast = self.factory.create_from_text("from abc import a\nx = a()\nz: a = x", "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py1.txt", ast)
        type_node = first(n for n in traverse(ast) if isinstance(n.ast_type(), Name) and n.name == "z")
        assert_that(type_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = type_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.ast_type(), instance_of(Name))
        assert_that(ref_node.name.lower(), is_("a"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))
        assert_that(type_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_class_reference(self):
        # Class A refers to Class B
        ast = self.factory.create_from_text(content3, "content3.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py2.txt", ast)

        class_node = first(n for n in traverse(ast) if isinstance(n.ast_type(), ClassDef) and n.name == "A")

        assert_that(class_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = class_node.references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.ast_type(), instance_of(ClassDef))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        assert_that(class_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_param_reference(self):
        # param obj refers to its type, if type definition in the same file, refers to def, otherwise refers to Name
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py3.txt", ast)

        param_node = [n for n in traverse(ast) if n.name == "bruno" and n.ast_type == Arg]

        assert_that(param_node[0], is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = param_node[0].references
        assert_that(refs, has_length(1))
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]
        assert_that(ref_node.ast_type(), instance_of(ClassDef))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(2))
        types = [r.node_id for r in referenced_by]
        assert_that(param_node[0].name, is_in(types))

    def test_function_reference(self):
        ast = self.factory.create_from_text(content, "content.py")
        with tempfile.TemporaryDirectory(delete=True) as temp_dir:
            syntax_tree.ASTShower.store_node(temp_dir + "/py4.txt", ast)
        call_node = first(n for n in traverse(ast) if isinstance(n.ast_type(), Call) and n.name == "bruno.is_near()")
        assert_that(call_node, is_(PythonRstNode))
        ast.translation_unit.lazy_create_refers(ast)
        refs = call_node.references
        ref = refs[0]
        ref_node = ast.translation_unit._nodes[ref.node_id]

        assert_that(ref_node.ast_type(), instance_of(FunctionDef))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(1))
        assert_that(call_node in [ast.translation_unit._nodes[r.node_id] for r in referenced_by])

    def test_references_to_a_builtin_type_do_not_crash(self):
        # `int` is not stored in `_nodes` (see the `types` exclusion list), so a reference to it
        # must not be resolved through that table.
        atu = self.factory.create_from_text("x: int = 0\n", "builtin.py")
        ann_assign = atu.children[0]
        assert_that([ref.node_id for ref in ann_assign.references], is_(["int"]))

    def test_function_references_its_return_type_annotation(self):
        # `Cat` is not called anywhere in the body, so only the annotation can produce this reference.
        atu = self.factory.create_from_text(returning_content, "returning.py")
        find_func = atu.children[1]
        assert_that([(ref.node_id, ref.ref_kind) for ref in find_func.references], is_([("Cat", "TypeRef")]))

    def test_class_is_referenced_by_a_function_returning_it(self):
        atu = self.factory.create_from_text(returning_content, "returning.py")
        cat_class = atu.children[0]
        assert_that([(ref.node_id, ref.ref_kind) for ref in cat_class.referenced_by], is_([("find", "TypeRef")]))

    def test_async_function_references_its_return_type_annotation(self):
        atu = self.factory.create_from_text(returning_content.replace("def find", "async def find"), "returning.py")
        find_func = atu.children[1]
        assert_that([(ref.node_id, ref.ref_kind) for ref in find_func.references], is_([("Cat", "TypeRef")]))

    def test_subscripted_return_annotation_is_not_recorded(self):
        # Only a bare `ast.Name` annotation is tracked, as in the `arg` and `AnnAssign` branches.
        atu = self.factory.create_from_text(returning_content.replace("-> Cat", "-> list[Cat]"), "returning.py")
        find_func = atu.children[1]
        assert_that(find_func.references, is_(empty()))

    def test_none_return_annotation_is_not_recorded(self):
        # `-> None` parses as an `ast.Constant`, not an `ast.Name`.
        atu = self.factory.create_from_text(returning_content.replace("-> Cat", "-> None"), "returning.py")
        find_func = atu.children[1]
        assert_that(find_func.references, is_(empty()))

    def test_ref_node_to_str(self):
        it = PythonRSTReference("it is ", "kind", {})
        assert_that(it, has_string("it is :kind"))


if __name__ == "__main__":
    pytest.main()
