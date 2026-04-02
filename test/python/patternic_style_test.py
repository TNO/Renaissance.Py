from operator import is_not

import pytest
from hamcrest import assert_that, is_, has_length, is_in, is_not, empty

from renaissance.impl import MATCH_ONE, MATCH_ALL
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.impl.python.factory import PythonFactory
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import is_match


class TestPythonicStyle:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonASTNode)
        self.pattern_factory = PythonPatternFactory(self.factory)
    @pytest.mark.parametrize(
        "raw, kind, op, name, expr, body_length",
        [
            ("try:\n  pass\nfinally:\n  pass", "Try", "try", "Try", "expr", 1),
            ("try:\n  x()\nexcept* e:\n  pass", "TryStar", "try", "TryStar", "expr", 1),
            ("class name: pass", "ClassDef", "class", "name", "expr", 1),
            ("def name(): pass", "FunctionDef", "function", "name", "expr", 1),
            ("for name in expr:\n  1\n  2\n  pass", "For", "for", "name", "expr", 3),
            ("while expr: pass", "While", "while", "While", "expr", 1),
            ("if expr: pass\nelse: pass ", "If", "if", "If", "expr", 1),
            ("match x:\n  case _:    pass", "Match", "match", "x", "expr", 1),
        ],
    )
    def test_consistent_name_stmt(self, raw, kind, op, name, expr, body_length):
        it = PythonASTNode.load_from_text(raw).body[-1]
        assert_that(it.kind, is_(kind))
        assert_that(it.operator, is_(op))
        assert_that(it.name, is_(name))
        # assert_that(it.expr.name, is_(expr))
        assert_that(it.body, has_length(body_length))

    

    @pytest.mark.parametrize(
        "raw, kind, op, name, body_length",
        [
            ("async for f in fs:  pass", "AsyncFor", "for", "f", 1),
            ('async with open("x"): pass', "AsyncWith", "with", "AsyncWith", 1),
            ("async def fun(): pass", "AsyncFunctionDef", "function", "fun", 1),
        ],
    )
    def test_async_stmt(self, raw, kind, op, name, body_length):
        it = PythonASTNode.load_from_text(raw).body[-1]
        assert_that(it.kind, is_(kind))
        assert_that(it.operator, is_(op))
        assert_that(it.name, is_(name))
        assert_that(it.body, has_length(body_length))

    @pytest.mark.parametrize(
        "raw, kind, name, body_length",
        [
            ("try:\n  1\n  x()\nexcept* e:\n  1\n  1\n  pass", "TryStar", "TryStar", 2),
            ("for name in expr:\n  1\n  2\n  pass", "For", "name", 3),
            ("while expr: pass", "While", "While", 1),
            ("if expr: pass\nelse: pass ", "If", "If", 1),
            ("match x:\n  case _:    pass", "Match", "x", 1),
        ],
    )
    def test_stmt_with_body(self, raw, kind, name, body_length):
        it = PythonASTNode.load_from_text(raw).body[-1]
        assert_that(kind, is_(it.kind))
        assert_that(it.name, is_(name))
        assert_that(it.body, has_length(body_length))

    @pytest.mark.parametrize(
        "raw, kind, typ, name, op, value",
        [
            ("i:int=0", "AnnAssign", "int", "i", "=", 0),
            ("i=0", "Assign", None, "i", "=", 0),
            ("x += 5", "AugAssign", None, "x", "+=", 5),
            ("break", "Break", None, "", "break", None),
            ("assert 0", "Assert", None, "", "assert", 0),
            ("continue", "Continue", None, "", "continue", None),
            ("import x", "Import", None, "x", "import", None),
            (
                "pass",
                "Pass",
                None,
                "",
                "pass",
                None,
            ),
        ],
    )
    def test_stmt(self, raw, kind, typ, name, op, value):


        it = PythonASTNode.load_from_text(raw).body[-1]
        assert_that(kind, is_(it.kind))
        assert_that(it.name, is_(name))
        assert_that(it.operator, op)
        assert_that(it.type, is_(typ))
        assert_that(it.value, is_(value))

    @pytest.mark.parametrize(
        "raw, kind, expr",
        [
            ("fun()", "Expr", "fun()"),
            ("return fun()", "Return", "fun()"),
            ("raise fun()", "Raise", "fun()"),
        ],
    )
    # ('from x import y', 'ImportFrom', None, 'x', 'import', 'y'),
    def test_expr(self, raw, kind, expr):
        it = PythonASTNode.load_from_text(raw).body[-1]
        assert_that(kind, is_(it.kind))
        assert_that(it.expr.name, is_(expr))

    def test_ann_assign_node(self):
        it = PythonASTNode.load_from_text('name:str = "value"').body[-1]

        assert_that(it.name, is_("name"))
        assert_that(it.type, is_("str"))
        assert_that(it.operator, is_("="))
        assert_that(it.value, is_("value"))

    def test_assign_node(self):
        

        it = PythonASTNode.load_from_text('name = "value"').body[-1]

        assert_that(it.name, is_("name"))
        assert_that(it.type, is_(None))
        assert_that(it.operator, is_("="))
        assert_that(it.value, is_("value"))

    def test_assign_node_2(self):

        it = PythonASTNode.load_from_text("name += 5").body[-1]
        assert_that(it.name, is_("name"))
        assert_that(it.type, is_(None))
        assert_that(it.operator, is_("+="))
        assert_that(it.value, is_(5))

    def python_does_not_parse_dollar(self):
        it = PythonASTNode.load_from_text("$pa")

        assert_that(MATCH_ONE, is_(it.kind))

    def python_does_not_parse_dollar(self):
        it = PythonASTNode.load_from_text("$$pa")
        assert_that(MATCH_ONE, is_(it.kind))

    def test_kind_is_match_all(self):
        pattern_factory = PythonPatternFactory(PythonFactory(PythonASTNode))
        simple = self.pattern_factory.create_statement("$$pa")
        assert_that(MATCH_ALL, is_(simple.kind))


    def test_kind_is_match_one(self):
        
        simple = self.pattern_factory.create_statement("$pa")
        assert_that(MATCH_ONE, is_(simple.kind))

    def test_kind_is_match_all(self):
        
        simple = self.pattern_factory.create_statement("$$pa")
        assert_that(MATCH_ALL, is_(simple.kind))


    def test_match_one_is_not_equal(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        pattern_factory = PythonPatternFactory(self.factory)
        match_one = self.pattern_factory.create("$pa")
        assert_that(atu.children[0], is_not(match_one))

    #  TODO contain is not dependent on pattern
    def test_is_match_all_stmt(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        
        match_all = self.pattern_factory.create("$$pa")
        assert_that(match_all.node, is_in(atu))

    def test_is_exact_match(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        

        stmt = PythonASTNode.load_from_text("ba(55)")[0]

        assert_that(atu.children[0], is_(stmt))

    def test_match_exact_pattern(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        
        stmt = self.pattern_factory.create_statement("ba(55)").node

        result = [node for node in atu if node == stmt]

        assert_that(result, has_length(1))

    def test_match_single_pattern(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        
        match_any = self.pattern_factory.create_statement("$stmt")

        result = [node for node in atu if node == match_any]
        assert_that(result, is_(empty()))

        result = [node for node in atu if is_match(node,match_any)]
        assert_that(result, has_length(4))

    def test_match_single_call_pattern(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        

        match_call = self.pattern_factory.create("$call($arg)")

        result = [node for node in atu if node == match_call]

        assert_that(result, has_length(0))

    def test_find_all_using_generic_matcher(self):
        
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        

        simple = self.pattern_factory.create_statement("ca(555)").node

        assert_that(atu[0], is_not(simple))
        assert_that(atu[1], is_(simple))
        assert_that(atu[2], is_not(simple))
        assert_that(atu[3], is_not(simple))

        result = [node for node in atu if node == simple]
        assert_that(result, has_length(1))

    def test_slice_call(self):
        
        atu = self.factory.create_from_text(
            "ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55",
            "test.py",
        )
        node_slice = atu[0:3]
        assert_that(node_slice, has_length(3))

    def test_property_kind_call(self):
        
        atu = self.factory.create_from_text(
            "ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55",
            "test.py",
        )
        kind = atu.kind
        assert_that(kind, is_("Module"))

    def test_property_name_call(self):
        
        atu = self.factory.create_from_text(
            "ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55",
            "test.py",
        )
        name = atu.name
        assert_that(name, is_("Module"))
