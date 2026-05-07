import ast
import textwrap
from pathlib import Path

import pytest
from hamcrest import (
    has_length,
    assert_that,
    is_in,
    is_,
    contains_string,
    empty,
    is_not,
)
from libcst import ParserSyntaxError

import targets

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.cst_node import PythonCstNode
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.utils.ast_utils import traverse


class TestPythonCstNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonCstNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_slice(self):
        it = self.pattern_factory.create_expression("items[1:2:3]")
        assert_that(it.children[0].kind, is_("Name"))
        assert_that(it.children[1].kind, is_("SimpleWhitespace"))
        assert_that(it.children[2].kind, is_("LeftSquareBracket"))
        assert_that(it.children[3].kind, is_("SubscriptElement"))
        assert_that(it.children[4].kind, is_("RightSquareBracket"))

    def test_attribute_signature_has_at(self):
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[0]
        assert_that(attr.signature, is_("@TUAT\n"))

    def test_node_family(self):
        src = PythonCstNode.load_from_text(
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
            "nav.py",
        )
        #          module  class     body        fun memem
        me = src.children[-1].children[5].children[2]
        assert_that(me.name, is_("mememe"))
        assert_that(me.preceding_sibling.name, is_("previous_me"))
        assert_that(me.next_sibling.name, is_("next_me"))
        assert_that(me.parent.parent.name, is_("Parent"))
        # all children are mashed together
        assert_that(me.children, has_length(8))

    def test_load_file_with_ignored_types(self):
        atu = PythonCstNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit, is_not(None))

    def test_load_file(self):
        atu = PythonCstNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu, is_not(None))

    def test_load_invalid_file(self):
        with pytest.raises(ParserSyntaxError, match="Syntax Error"):
            PythonCstNode.load(Path(targets.__file__).parent / "invalid.py")

    def test_ann_fun_to_str2(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    
        matches = match_pattern( func_body.children,patterns)
    
        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonCstNode.load_from_text(ann_fun, "fun.py").children[-1]
        assert_that(it.offset, is_(1))
        assert_that(it.signature, contains_string("@parameterized.expand"))

    def test_ann_fun_to_str(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    
        matches = match_pattern( func_body.children,patterns)
    
        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonCstNode.load_from_text(ann_fun, "fun.py").children[-1]
        assert_that(it.signature, contains_string("def test"))
