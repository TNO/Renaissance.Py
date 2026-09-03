import textwrap
from pathlib import Path

import hypothesmith
import libcst
import pytest
from hamcrest import (
    assert_that,
    contains_string,
    empty,
    has_length,
    instance_of,
    is_,
)
from hypothesis import HealthCheck, given, settings

import targets
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.types import *
from renaissance.syntax_tree import ASTShower
from utils_for_tests import reject_unsupported_code


class TestPythonRstNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_type_alias(self):
        it = self.factory.create_from_text("type UserId = int", "context.py")
        assert_that(it.children[0].ast_type(), is_(TypeAlias))

    def test_slice(self):
        it = self.pattern_factory.create_expression("items[1:2:3]")
        assert_that(it.children[1].ast_type(), is_(Slice))

    def test_named_expr(self):
        it = self.pattern_factory.create_statement("if n:= len(items): pass")
        assert_that(it.children[0].ast_type(), is_(NamedExpr))

    def test_named_expr_simple(self):
        it = self.pattern_factory.create_statement("(n:= 3)")
        assert_that(it.children[0].ast_type(), is_(NamedExpr))

    # why not ""?
    def test_starred(self):
        it = self.pattern_factory.create_statement("*x =[1,2]")
        assert_that(it.children[0].children[0].ast_type(), is_(Starred))

    def test_formatted_value(self):
        it = self.pattern_factory.create_expression('f"{one}two"')
        assert_that(it.children[0].ast_type(), is_(FormattedString))

    def test_except_handler(self):
        it = self.pattern_factory.create_statement("try: pass\nexcept NameError:pass")
        assert_that(it.children[1].children[0].ast_type(), is_(Catch))

    def test_match_stmt(self):
        sample_code = (
            'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        )
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(stmt.ast_type(), is_(Match))
        assert_that(stmt.children[1].children[0].ast_type(), is_(MatchCase))
        assert_that(stmt.children[1].children[0].children[0].children[1].ast_type(), is_(MatchStar))
        assert_that(stmt.children[1].children[0].children[0].children[0].ast_type(), is_(MatchAs))

    def test_show_call(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "apple.py")
        second_stmt = atu.children[1]
        assert_that(second_stmt.offset, is_(7))
        assert_that(second_stmt.length, is_(7))
        assert_that(second_stmt.filename, is_("apple.py"))
        assert_that(atu.translation_unit, is_(second_stmt.translation_unit))

    def test_attribute_signature_has_at(self):
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[2].children[0]
        assert_that(attr.signature, is_("@TUAT"))

    def test_node_family(self):
        src = PythonRstNode.load_from_text(
            textwrap.dedent("""
import you
from other import dog
class Parent:
    def previous_me():
        pass
    def mememe(a55,a66,a77,a88,a99):
        l(a55)
        l(a66)
        l(a77)
        l(a88)
    def next_me():
        pass
    """),
        )
        #          module  class     body        fun memem
        me = src.children[-1].children[2].children[1]
        assert_that(me.name, is_("mememe"))
        assert_that(me.preceding_sibling.name, is_("previous_me"))
        assert_that(me.next_sibling.name, is_("next_me"))
        assert_that(me.parent.parent.name, is_("Parent"))
        assert_that(me.children[1].children, has_length(4))

    @pytest.mark.skip("don't use ast comment parser")
    def test_load_file_with_ignored_types(self):
        atu = PythonRstNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit.atu.type_ignores, has_length(1))

    def test_load_file(self):
        atu = PythonRstNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu.translation_unit.atu.type_ignores, is_(empty()))

    def test_load_invalid_file(self):
        with pytest.raises(IndentationError, match="unexpected indent"):
            PythonRstNode.load(Path(targets.__file__).parent / "invalid.py")

    def test_ann_fun_to_str2(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")

        matches = match_pattern( func_body.children,patterns)

        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonRstNode.load_from_text(ann_fun).body[-1]
        assert_that(it.offset, is_(1))
        assert_that(it.signature, contains_string("@parameterized.expand"))

    # @pytest.mark.skip("it was working before")
    def test_ann_fun_to_str(self):
        ann_fun = textwrap.dedent("""
        @parameterized.expand(Factories.extend(['$x;$y;']))
        def test(_):
            atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")

            matches = match_pattern( func_body.children,patterns)

            self.assert_matches( expected_dicts_per_match,matches)
            """)
        it = PythonRstNode.load_from_text(ann_fun).body[-1]

        assert_that("\n" + it.signature + "\n", is_(ann_fun))

    @pytest.mark.hypothesisslow
    @given(code=hypothesmith.from_node(libcst.BaseStatement))
    @settings(max_examples=50, suppress_health_check=list(HealthCheck))
    def test_from_cst_returns_statement(self, code):
        reject_unsupported_code(code)
        factory = PythonFactory(PythonRstNode)
        node = factory.create_from_text(code)
        print(f"testing {code=} with PythonRstNode")
        assert_that(node.children[0].ast_type(), instance_of(Statement), f"{code=}")

    def test_corner_case(self):
        factory = PythonFactory(PythonRstNode)
        node = factory.create_from_text("class ŻP𭻊鲖ÉØ_ąň𣑗: pass\n")
        assert_that(node.children[0].ast_type(), instance_of(Statement))
