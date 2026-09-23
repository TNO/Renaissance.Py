"""Tests for the RST-based Python AST node implementation."""

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
    is_,
)
from hypothesis import HealthCheck, given, settings
from pytest_mock import MockerFixture

import targets
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTShower
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import traverse
from utils_for_tests import reject_unsupported_code


class TestPythonRstNode:
    """AI: Tests for the RST-based Python AST node implementation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """AI: Build the shared Python factory, sample AST, and pattern factory used by the RST node tests."""
        self.factory = PythonFactory(PythonRstNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_type_alias(self):
        """AI: Verify a type-alias statement parses with parser kind 'TypeAlias'."""
        it = self.factory.create_from_text("type UserId = int", "context.py")
        assert_that(it.children[0].parser_kind, is_("TypeAlias"))

    def test_exposes_parser_and_semantic_kinds(self):
        """AI: Verify a function definition's nodes expose the expected parser and semantic kinds for function, parameter, and name."""
        root = self.factory.create_from_text("def f(value):\n    return value\n")
        function = root.children[0]
        parameter = function.children[0].children[1].children[0]
        returned_name = function.children[1].children[0].children[0]

        assert function.parser_kind == "FunctionDef"
        assert function.semantic_kind is SemanticKind.FUNCTION
        assert parameter.semantic_kind is SemanticKind.PARAMETER
        assert returned_name.semantic_kind is SemanticKind.NAME

    def test_unknown_python_kind_keeps_parser_name(self):
        """AI: Verify a set literal keeps its parser kind 'Set' while its semantic kind falls back to NODE."""
        root = self.factory.create_from_text("x = {1, 2}")
        set_node = root.children[0].children[1]

        assert set_node.parser_kind == "Set"
        assert set_node.semantic_kind is SemanticKind.NODE

    def test_slice(self):
        """AI: Verify a subscript slice expression's second child has parser kind 'Slice'."""
        it = self.pattern_factory.create_expression("items[1:2:3]")
        assert_that(it.children[1].parser_kind, is_("Slice"))

    def test_named_expr(self):
        """AI: Verify a walrus-operator condition in an if-statement parses with parser kind 'NamedExpr'."""
        it = self.pattern_factory.create_statement("if n:= len(items): pass")
        assert_that(it.children[0].parser_kind, is_("NamedExpr"))

    def test_named_expr_simple(self):
        """AI: Verify a bare walrus-operator expression parses with parser kind 'NamedExpr'."""
        it = self.pattern_factory.create_statement("(n:= 3)")
        assert_that(it.children[0].parser_kind, is_("NamedExpr"))

    # why not ""?
    def test_starred(self):
        """AI: Verify a starred-unpacking assignment target parses with parser kind 'Starred'."""
        it = self.pattern_factory.create_statement("*x =[1,2]")
        assert_that(it.children[0].children[0].parser_kind, is_("Starred"))

    def test_formatted_value(self):
        """AI: Verify an f-string's embedded expression parses with parser kind 'FormattedValue'."""
        it = self.pattern_factory.create_expression('f"{one}two"')
        assert_that(it.children[0].parser_kind, is_("FormattedValue"))

    def test_except_handler(self):
        """AI: Verify a try/except statement's except clause parses with parser kind 'ExceptHandler'."""
        it = self.pattern_factory.create_statement("try: pass\nexcept NameError:pass")
        assert_that(it.children[1].children[0].parser_kind, is_("ExceptHandler"))

    def test_match_stmt(self):
        """AI: Verify a match-case statement with sequence unpacking parses with the expected nested parser kinds."""
        sample_code = (
            'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        )
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(stmt.parser_kind, is_("Match"))
        assert_that(stmt.children[1].children[0].parser_kind, is_("match_case"))
        assert_that(stmt.children[1].children[0].children[0].children[1].parser_kind, is_("MatchStar"))
        assert_that(stmt.children[1].children[0].children[0].children[0].parser_kind, is_("MatchAs"))

    def test_show_call(self):
        """AI: Verify a statement node exposes correct offset, length, filename, and shared translation unit."""
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "apple.py")
        second_stmt = atu.children[1]
        assert_that(second_stmt.offset, is_(7))
        assert_that(second_stmt.length, is_(7))
        assert_that(second_stmt.filename, is_("apple.py"))
        assert_that(atu.translation_unit, is_(second_stmt.translation_unit))

    def test_attribute_signature_has_at(self):
        """AI: Verify a decorated function's decorator node signature includes the leading @ syntax."""
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[2].children[0]
        assert_that(attr.signature, is_("@TUAT"))

    def test_node_family(self):
        """AI: Verify a method node exposes its name, sibling methods, parent class, and children count."""
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
        """AI: Verify loading source with a '# type: ignore' comment records it in the AST's type_ignores."""
        atu = PythonRstNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit.atu.type_ignores, has_length(1))

    def test_load_file(self):
        """AI: Verify loading a demo Python file from disk produces no type_ignores."""
        atu = PythonRstNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu.translation_unit.atu.type_ignores, is_(empty()))

    def test_load_invalid_file(self):
        """AI: Verify loading a syntactically invalid Python file raises an IndentationError."""
        with pytest.raises(IndentationError, match="unexpected indent"):
            PythonRstNode.load(Path(targets.__file__).parent / "invalid.py")

    def test_load_file_with_non_cp1252_bytes(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """A UTF-8 file with bytes undefined in cp1252 loads even when the locale default is cp1252."""
        # `Ё` (U+0401) encodes to UTF-8 bytes D0 81; 0x81 is undefined in cp1252, so reading this
        # file without an explicit UTF-8 encoding raises UnicodeDecodeError on Windows.
        file_path = tmp_path / "non_cp1252.py"
        file_path.write_text("# Ё\nx = 1\n", encoding="utf-8")
        mocker.patch("locale.getpreferredencoding", return_value="cp1252")

        atu = PythonRstNode.load(file_path)

        assert_that(atu.translation_unit.atu.type_ignores, is_(empty()))

    def test_ann_fun_to_str2(self):
        """AI: Verify a decorated function's offset and signature reflect the leading decorator text."""
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
        """AI: Verify a decorated function's signature round-trips back to the original source text."""
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
        """AI: Verify creating a node from arbitrary hypothesis-generated code yields a non-NODE-kind child."""
        reject_unsupported_code(code)
        factory = PythonFactory(PythonRstNode)
        node = factory.create_from_text(code)
        print(f"testing {code=} with PythonRstNode")
        assert_that(node.children[0].semantic_kind is not SemanticKind.NODE, is_(True), f"{code=}")

    def test_corner_case(self):
        """AI: Verify a class name made of exotic unicode characters yields a non-NODE-kind child."""
        factory = PythonFactory(PythonRstNode)
        node = factory.create_from_text("class ŻP𭻊鲖ÉØ_ąň𣑗: pass\n")
        assert_that(node.children[0].semantic_kind is not SemanticKind.NODE, is_(True))

    @pytest.mark.parametrize(
        "code, expected_kind",
        [
            ("for a, (b, c) in x():\n    pass\n", "For"),
            ("for (a, b), c in x():\n    pass\n", "For"),
            ("async def f():\n    async for a, (b, c) in x():\n        pass\n", "AsyncFor"),
        ],
    )
    def test_nested_tuple_unpacking_for_target(self, code, expected_kind, capsys):
        """AI: Verify nested-tuple for-loop targets parse without AttributeError and produce the expected kind."""
        root = PythonRstNode.load_from_text(code)

        assert expected_kind in [c.parser_kind for c in traverse(root)]
        assert "has no attribute" not in capsys.readouterr().out

    @pytest.mark.parametrize(
        "code, expected_kind",
        [
            ("global x\n", "Global"),
            ("global x, y\n", "Global"),
            ("def f():\n    def g():\n        nonlocal x\n", "Nonlocal"),
        ],
    )
    def test_global_nonlocal_names_not_dropped(self, code, expected_kind, capsys):
        """AI: Verify global/nonlocal statements keep their names without raising AttributeError."""
        root = PythonRstNode.load_from_text(code)

        assert expected_kind in [c.parser_kind for c in traverse(root)]
        assert "has no attribute" not in capsys.readouterr().out

    @pytest.mark.xfail(
        reason="PythonRstNode does not inherit from ASTNode, so get_ancestor() is not available on it",
        strict=True,
    )
    def test_get_ancestor_finds_enclosing_function(self):
        """get_ancestor() walks up .parent to find the nearest FunctionDef."""
        root = PythonRstNode.load_from_text("def f():\n    x = 1\n")
        target = root.children[0].children[0]
        ancestor = target.get_ancestor("FunctionDef")
        assert ancestor is not None
        assert ancestor.parser_kind == "FunctionDef"
