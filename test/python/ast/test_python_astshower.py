"""Tests for rendering Python AST nodes via ASTShower."""

import pytest
from hamcrest import assert_that, contains_string, not_, starts_with

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTShower


class TestPythonShower:
    """AI: Tests for rendering Python AST nodes via ASTShower."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """AI: Build the shared Python factory, sample AST, and pattern factory used by the ASTShower tests."""
        self.factory = PythonFactory(PythonRstNode)
        self.atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_show_call_using_repr(self):
        """AI: Verify rendering a call pattern shows its parser kind and placeholder-mangled names."""
        pattern = self.pattern_factory.create_statement("$pa($55)")
        text = ASTShower.get_node(pattern.node, display_parser_kind=True)
        assert_that(text, contains_string("(Expr,"))
        assert_that(text, contains_string("_MatchOne__pa(_MatchOne__55)"))

    def test_show_module(self):
        """AI: Verify rendering the module node starts with its parser kind and contains the source text."""
        text = ASTShower.get_node(self.atu, display_parser_kind=True)
        assert_that(text, starts_with("(Module,"))
        assert_that(text, contains_string("ba(55)"))

    def test_show_body(self):
        """AI: Verify stringifying the module's children includes the source text."""
        assert_that(str(self.atu.children), contains_string("ba(55)"))

    def test_show_ast_filter_implicit_node(self):
        """AI: Verify rendering without parser kinds omits implicit-node markers."""
        ptext = ASTShower.get_node(self.atu)
        assert_that(ptext, not_(contains_string("(ImplicitNode")))

    def test_show_ast(self):
        """AI: Verify rendering the module shows nested call/name/constant nodes with their parser kinds."""
        text = ASTShower.get_node(self.atu, display_parser_kind=True)
        assert_that(text, contains_string("(Module,"))
        assert_that(text, contains_string("(Call, ba(55),"))
        assert_that(text, contains_string("(Name, ba,"))
        assert_that(text, contains_string("(Constant, 55,"))

    def test_show_if_else(self):
        """AI: Verify rendering an if/else statement's AST produces the expected node structure."""
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text(
            """
if x >y :
    x=1
    call(x)
else:
    y=1
    call(y)
            """,
            "test.py",
        )
        text = ASTShower.get_node(atu.children[0], display_parser_kind=True)
        assert_that(text, contains_string("(If, If,"))
        assert_that(text, contains_string("(Compare, x > y,"))
        assert_that(text, contains_string("(Call, call(x),"))
        assert_that(text, contains_string("test.py[15:18]"))
        assert_that(text, contains_string("call(y)"))


if __name__ == "__main__":
    pytest.main()
