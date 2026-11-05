# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the CST-based Python AST node implementation."""

import textwrap
from pathlib import Path

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    has_length,
    has_properties,
    has_property,
    is_,
    is_not,
)
from libcst import ParserSyntaxError

import targets
from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree import ASTShower


class TestPythonCstNode:
    """AI: Tests for the CST-based Python AST node implementation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """AI: Build the CST-backed Python factory, sample AST, and pattern factory used by the CST node tests."""
        self.factory = PythonFactory(PythonCstNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_slice(self) -> None:
        """AI: Verify a subscript slice expression's children expose the expected CST parser kinds in order."""
        it = self.pattern_factory.create_expression("items[1:2:3]")

        assert_that(it.children[0].parser_kind, is_("Name"))
        assert_that(it.children[1].parser_kind, is_("SimpleWhitespace"))
        assert_that(it.children[2].parser_kind, is_("LeftSquareBracket"))
        assert_that(it.children[3].parser_kind, is_("SubscriptElement"))
        assert_that(it.children[4].parser_kind, is_("RightSquareBracket"))

    def test_attribute_signature_has_at(self) -> None:
        """AI: Verify a decorated function's decorator node signature includes the leading @ syntax."""
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[0]
        assert_that(attr.signature, is_("@TUAT\n"))

    def test_node_family(self) -> None:
        """AI: Verify a method node exposes its name, sibling methods, parent class, and children count."""
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
        assert_that(
            me,
            has_properties(
                name="mememe",
                preceding_sibling=has_property("name", "previous_me"),
                next_sibling=has_property("name", "next_me"),
                parent=has_property("parent", has_property("name", "Parent")),
            ),
        )
        # all children are mashed together
        assert_that(me.children, has_length(8))

    def test_load_file_with_ignored_types(self) -> None:
        """AI: Verify loading source with a '# type: ignore' comment still produces a valid translation unit."""
        atu = PythonCstNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit, is_not(None))

    def test_load_file(self) -> None:
        """AI: Verify loading a demo Python file from disk produces a valid node."""
        atu = PythonCstNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu, is_not(None))

    def test_load_invalid_file(self) -> None:
        """AI: Verify loading a syntactically invalid Python file raises a ParserSyntaxError."""
        with pytest.raises(ParserSyntaxError, match="Syntax Error"):
            PythonCstNode.load(Path(targets.__file__).parent / "invalid.py")

    def test_ann_fun_to_str2(self) -> None:
        """AI: Verify a decorated function's offset and signature reflect the leading decorator text."""
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

    def test_ann_fun_to_str(self) -> None:
        """AI: Verify a decorated function's signature includes the function definition text."""
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")

        matches = match_pattern( func_body.children,patterns)

        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonCstNode.load_from_text(ann_fun, "fun.py").children[-1]
        assert_that(it.signature, contains_string("def test"))


class _SubclassNode(PythonCstNode):
    """A PythonCstNode subclass that adds nothing."""


@pytest.mark.parametrize(
    "source",
    [
        "a = 0\n",
        "class A:\n    def f(self): pass\n    def g(self): pass\n",
        "@decorator\ndef f(x):\n    return x + 1\n",
        "items = [n * 2 for n in range(10) if n % 3]\n",
    ],
)
def test_load_builds_every_node_from_the_subclass(source: str, tmp_path: Path) -> None:
    """Verify a subclass's load yields a tree whose nodes, roots, parents and siblings are all of that subclass."""
    file = tmp_path / "module.py"
    file.write_text(source, encoding="utf-8", newline="\n")
    pending: list[PythonCstNode] = [_SubclassNode.load(file)]
    while pending:
        node = pending.pop()
        for related in (node, node.root, node.parent, node.next_sibling, node.preceding_sibling):
            if related is not None:
                assert_that(related, is_(_SubclassNode))
        pending.extend(node.children)
