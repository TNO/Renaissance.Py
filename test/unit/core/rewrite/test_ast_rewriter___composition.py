# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the ASTRewriter: composing replacements from matches, and combining several rewrites."""

import sys
from collections.abc import Callable

import pytest
from hamcrest import assert_that, has_length, is_
from pytest_mock import MockerFixture

from renaissance.core.match import PatternMatch, find_all, match_pattern
from renaissance.core.model import ASTFactory
from renaissance.core.rewrite import ASTRewriter
from renaissance.core.rewrite.ast_rewriter import _RewriteAction, _RewriteActions
from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from test.unit.shared.factories import Factories
from test.unit.shared.utils_for_tests import compress


class TestComposeReplacement:
    """AI: Tests composing a replacement pattern from a match's placeholder bindings."""

    @pytest.mark.parametrize(
        ("_", "factory", "statements", "extra_declarations", "replacement"),
        Factories.extend(
            [
                (
                    "if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}",
                    [],
                    {"$$before; b = ($exp) ? $d1:$d2; $$after;": "int a=1;int b=2;int c=3;int d=4;void f(){c++;b=(a==1)?2:3;d++;}"},
                ),
            ],
        ),
    )
    def test_args(
        self,
        _: str,
        factory: ASTFactory,
        statements: str,
        extra_declarations: list[str],
        replacement: dict[str, str],
    ) -> None:
        """AI: Verify replace rewrites a matched if/else pattern into a ternary assignment using the placeholder bindings."""
        code = """
            int a = 1;
            int b = 2;
            int c = 3;
            int d = 4;
            void f(){
                if (a==1) {
                    c++;
                    b = 2;
                    d++;
                }
                else {
                    c++;
                    b = 3;
                    d++;
                }
            }
            """
        atu = factory.create_from_text(code, "test.cpp")
        stmt_nodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = list(match for match in match_pattern([atu], stmt_nodes) if match.nodes[0].is_part_of_translation_unit())
        assert_that(matches, has_length(1), "Expected one match")
        assert_that(replacement.items(), has_length(1), "Expected one replacement item")
        for match, exp in zip(matches, replacement.items(), strict=True):
            rewriter = ASTRewriter(match.nodes[0].root)
            org, expected = exp
            rewriter.replace(org, match)
            actual = rewriter.apply_to_string()
            assert_that(compress(expected), is_(compress(actual)))

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("def f():\n    x = compute(1, 2)\n    return x\n", "def f():\n    y = compute(1, 2)\n    x = y\n    return x\n"),
            ("def f():\n    x = [1, 2]\n    return x\n", "def f():\n    y = [1, 2]\n    x = y\n    return x\n"),
        ],
    )
    def test_python_placeholder_replacement(self, source: str, expected: str) -> None:
        """Verify replacing a PatternMatch on a Python tree expands its placeholders into the new text."""
        root = PythonRstNode.load_from_text(source, "test.py")
        pattern = PythonPatternFactory(PythonFactory(PythonRstNode)).create_statements("x = $value")
        rewriter = ASTRewriter(root)
        for match in match_pattern([root], pattern):
            rewriter.replace("y = $value\nx = y", match, include_whitespace=False, include_comments=False)
        assert_that(rewriter.apply_to_string(), is_(expected))

    @pytest.mark.parametrize(
        ("source", "find", "replacement", "expected"),
        [
            (
                "if TYPE_CHECKING:\n    from a import X\n    import b as B\n\n\ndef f(x: X) -> B.Y: ...\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                "from a import X\nimport b as B\n\n\ndef f(x: X) -> B.Y: ...\n",
            ),
            (
                "def f():\n    if TYPE_CHECKING:\n        first()\n        second()\n        third()\n    return 0\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                "def f():\n    first()\n    second()\n    third()\n    return 0\n",
            ),
            (
                "if TYPE_CHECKING:\n    from a import (\n        X,  # x\n        Y,\n    )\n    import b\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                "from a import (\n    X,  # x\n    Y,\n)\nimport b\n",
            ),
            (
                "if TYPE_CHECKING:\n    from a import X  # café\n    import b\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                "from a import X  # café\nimport b\n",
            ),
            ("f(1, 2)\n", "f($$args)", "g($$args)", "g(1, 2)\n"),
        ],
    )
    def test_python_multi_node_placeholder(self, source: str, find: str, replacement: str, expected: str) -> None:
        """Verify a `$$` placeholder bound to several nodes expands to all of them, keeping their text and layout."""
        root = PythonRstNode.load_from_text(source, "test.py")
        pattern = PythonPatternFactory(PythonFactory(PythonRstNode)).create_statements(find)
        rewriter = ASTRewriter(root)
        for match in match_pattern([root], pattern):
            rewriter.replace(replacement, match, include_whitespace=False, include_comments=False)
        assert_that(rewriter.apply_to_string(), is_(expected))

    @pytest.mark.parametrize(
        ("source", "find", "replacement", "transforms", "expected"),
        [
            (
                "if TYPE_CHECKING:\n    from a import X\n    import b as B\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                {"$$includes": "lazy {}".format},
                "lazy from a import X\nlazy import b as B\n",
            ),
            (
                "if TYPE_CHECKING:\n    from a import (\n        X,  # x\n        Y,\n    )\n    import b\n",
                "if TYPE_CHECKING:\n    $$includes",
                "$$includes",
                {"$$includes": "lazy {}".format},
                "lazy from a import (\n    X,  # x\n    Y,\n)\nlazy import b\n",
            ),
            ("f(a, b)\n", "f($x, $y)", "g($y, $x)", {"$x": str.upper}, "g(b, A)\n"),
        ],
    )
    def test_python_placeholder_transform(
        self, source: str, find: str, replacement: str, transforms: dict[str, Callable[[str], str]], expected: str
    ) -> None:
        """Verify `transforms` rewrites the text of each node bound to its placeholder, and leaves other placeholders as they are."""
        root = PythonRstNode.load_from_text(source, "test.py")
        pattern = PythonPatternFactory(PythonFactory(PythonRstNode)).create_statements(find)
        rewriter = ASTRewriter(root)
        for match in match_pattern([root], pattern):
            rewriter.replace(replacement, match, include_whitespace=False, include_comments=False, transforms=transforms)
        assert_that(rewriter.apply_to_string(), is_(expected))

    @pytest.mark.xfail(strict=True, reason="the outer apply() also applies the nested rewrite, see issue #286")
    def test_python_multi_node_placeholder_with_nested_rewrite(self) -> None:
        """Verify a rewrite inside one of the nodes bound to a `$$` placeholder is kept when the placeholder expands."""
        root = PythonRstNode.load_from_text("def f():\n    if TYPE_CHECKING:\n        first()\n        second()\n    return 0\n", "test.py")
        pattern = PythonPatternFactory(PythonFactory(PythonRstNode)).create_statements("if TYPE_CHECKING:\n    $$includes")
        match = match_pattern([root], pattern)[0]
        callee = match.expansions["$$includes"][1].children[0].children[0]
        rewriter = ASTRewriter(root)
        rewriter.replace("two", callee, include_whitespace=False, include_comments=False)
        rewriter.replace("$$includes", match, include_whitespace=False, include_comments=False)
        assert_that(rewriter.apply_to_string(), is_("def f():\n    first()\n    two()\n    return 0\n"))

    @pytest.mark.parametrize(
        "factory",
        [
            pytest.param(
                factory,
                id=name,
                marks=[
                    pytest.mark.xfail(
                        sys.platform == "win32",
                        strict=True,
                        reason="clang_json sends the code to clang with CRLF line endings on Windows, so offsets shift",
                    )
                ]
                if name == "clang_json"
                else [],
            )
            for name, factory in Factories.factories
        ],
    )
    def test_c_multi_statement_placeholder(self, factory: ASTFactory) -> None:
        """Verify a `$$` placeholder bound to several C statements expands to all of them."""
        code = "int a = 1;\nint c = 2;\nint d = 3;\nvoid f(){\n    if (a) {\n        c++;\n        d++;\n    }\n}\n"
        atu = factory.create_from_text(code, "test.cpp")
        pattern = CPatternFactory(factory).create_statements("if($e){$$body;}")
        matches = [match for match in match_pattern([atu], pattern) if match.nodes[0].is_part_of_translation_unit()]
        assert_that(matches, has_length(1), "Expected one match")
        rewriter = ASTRewriter(atu)
        rewriter.replace("$$body;", matches[0])
        assert_that(compress(rewriter.apply_to_string()), is_(compress("int a=1;int c=2;int d=3;void f(){c++;d++;}")))

    def test_get_node_in_match_pattern(self, mocker: MockerFixture) -> None:
        """AI: Verify _RewriteAction._get_nodes resolves a node's referenced_by chain back to the original node."""
        node = mocker.Mock()
        reference = mocker.Mock()
        node.referenced_by = [reference, reference]
        reference.node = node
        pattern_match = PatternMatch([node, node, node], {}, [])
        n = _RewriteAction._get_nodes([pattern_match])[0]
        assert_that(n, is_(node))

    @pytest.mark.skip("fail on empty nodes")
    def test_get_node_in_match_pattern_on_empty_pattern(self) -> None:
        """AI: Verify __get_texts raises/returns gracefully when given an empty node list (currently fails)."""
        it = _RewriteActions([], sys.getfilesystemencoding(), True)
        text = it._RewriteActions__get_texts([])
        assert_that(text, is_("node"))

    def test_get_text_from_rewrite(self, mocker: MockerFixture) -> None:
        """AI: Verify __get_texts extracts the node's text slice from its binary file content."""
        node = mocker.Mock()
        node.root = node
        node.binary_file_content = lambda: b"int x =0;"
        node.offset = 0
        node.extended_end_offset = 8
        node.text = "int x =0"

        it = _RewriteActions(node, sys.getfilesystemencoding(), True)
        text = it._RewriteActions__get_texts([node])
        assert_that(text, is_("int x =0"))


class TestAroundComposition:
    """Test case to capture the requirements for `around` functionality that is composable."""

    @pytest.mark.skip(
        "TODO: Test fails due to two issues\n  1. order of inserts ([  )]\n  2. insert around whole pattern, not placeholder.",
    )
    def test_around(self) -> None:
        """AI: Verify two composed insert_before/insert_after pairs around the same placeholder nest correctly (currently fails)."""
        # set up
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text("x = a", "temp.py")
        pattern = PythonPatternFactory(factory).create_expression("x = $a")
        matches = list(find_all([atu], [pattern]))  # Use list, since we want to access its content multiple times
        assert matches, "A match expected"
        nrof_matches = len(matches)
        assert nrof_matches == 1, f"One match expected, yet got {nrof_matches}"
        placeholder = matches[0].expansions["$a"]

        rewriter = ASTRewriter(atu)

        # execute
        ## first pair
        rewriter.insert_before("(", placeholder)
        rewriter.insert_after(")", placeholder)

        ## second pair
        rewriter.insert_before("[", placeholder)
        rewriter.insert_after("]", placeholder)

        # verify
        assert_that(rewriter.apply_to_string(), is_("x = [ ( a ) ]"), "Unexpected replacement")


class TestContainedOperations:
    """Test case to capture the requirements for a (completely) contained operation: it is ignore.

    See https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-contained-changes
    """

    def setup(self) -> tuple[ASTRewriter, PatternMatch]:
        """AI: Build a rewriter and a single match for the expression 'x = a * b' against pattern '$a * $b'."""
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text("x = a * b", "temp.py")
        pattern = PythonPatternFactory(factory).create_expression("$a * $b")
        matches = list(find_all([atu], [pattern]))  # Use list, since we want to access its content multiple times
        assert matches, "A match expected"
        nrof_matches = len(matches)
        assert nrof_matches == 1, f"One match expected, yet got {nrof_matches}"
        match = matches[0]

        rewriter = ASTRewriter(atu)
        return rewriter, match

    @pytest.mark.skip("TODO: fix impl.")
    def test_replace_contained_replace(self) -> None:
        """AI: Verify replacing the parent then the contained child collapses to the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.replace("product", match.nodes)
        rewriter.replace("term", match.expansions["$a"])
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_contained_replace_replace(self) -> None:
        """AI: Verify replacing the contained child then the parent collapses to the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.replace("term", match.expansions["$a"])
        rewriter.replace("product", match.nodes)
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_replace_contained_remove(self) -> None:
        """AI: Verify replacing the parent then removing a contained child leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.replace("product", match.nodes)
        rewriter.remove(match.expansions["$a"])
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_contained_remove_replace(self) -> None:
        """AI: Verify removing a contained child then replacing the parent leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.remove(match.expansions["$a"])
        rewriter.replace("product", match.nodes)
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_replace_contained_prepend(self) -> None:
        """AI: Verify replacing the parent then prepending to a contained child leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.replace("product", match.nodes)
        rewriter.insert_before("term", match.expansions["$a"])
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_contained_prepend_replace(self) -> None:
        """AI: Verify prepending to a contained child then replacing the parent leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.insert_before("term", match.expansions["$a"])
        rewriter.replace("product", match.nodes)
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_replace_contained_append(self) -> None:
        """AI: Verify replacing the parent then appending to a contained child leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.replace("product", match.nodes)
        rewriter.insert_after("term", match.expansions["$a"])
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"

    @pytest.mark.skip("TODO: fix impl.")
    def test_contained_append_replace(self) -> None:
        """AI: Verify appending to a contained child then replacing the parent leaves only the parent's replacement (currently fails)."""
        rewriter, match = self.setup()
        rewriter.insert_after("term", match.expansions["$a"])
        rewriter.replace("product", match.nodes)
        assert rewriter.apply_to_string() == "x = product", "Unexpected replacement"


class TestOverlappingOperations:
    """Test case to capture the requirements for partly overlapping operations: an exception is raised.

    See https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-overlapping-changes
    """

    def setup(self) -> tuple[ASTRewriter, PatternMatch]:
        """AI: Build a rewriter and a single match for 'def f(a,b,c): pass' against pattern 'def f($a,$b,$c): pass'."""
        code: str = """
def f(a,b,c):
    pass
"""

        pattern: str = """
def f($a,$b,$c):
    pass
"""

        factory = ASTFactory(PythonRstNode, [])
        atu = factory.create_from_text(code, "temp.py")
        pattern = PythonPatternFactory(factory).create(pattern)
        matches = list(find_all([atu], [pattern]))  # Use list, since we want to access its content multiple times
        assert matches, "A match expected"
        nrof_matches = len(matches)
        assert nrof_matches == 1, f"One match expected, yet got {nrof_matches}"
        match = matches[0]

        rewriter = ASTRewriter(atu)
        return rewriter, match

    @pytest.mark.skip(
        "it is not correctly implementing: https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-contained-changes",
    )
    def test_overlapping_replaces(self) -> None:
        """AI: Verify apply_to_string raises when two replace operations target partially overlapping placeholder ranges."""
        rewriter, match = self.setup()
        placeholder_a = match.expansions["$a"]
        placeholder_b = match.expansions["$b"]
        placeholder_c = match.expansions["$c"]

        rewriter.replace("any", [placeholder_a, placeholder_b])
        rewriter.replace("ANY", [placeholder_b, placeholder_c])

        with pytest.raises(Exception):
            rewriter.apply_to_string()


class TestSyntaxAwareNestedComposition:
    """Test Class for Syntax Aware Nested / Hierarchical Compositions.

    In Python
    * Prepend before parent and (first) child
      See https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-combination-of-multiple-prepends
    * Append after parent and (last) child
      See https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-combination-of-multiple-appends.
    """

    def setup(self) -> tuple[ASTRewriter, PatternMatch]:
        """AI: Build a rewriter and a single match for the expression 'x = a * b' against pattern '$a * $b'."""
        factory = ASTFactory(PythonRstNode, [])
        atu = factory.create_from_text("x = a * b", "temp.py")
        pattern = PythonPatternFactory(factory).create_expression("$a * $b")
        matches = list(find_all([atu], [pattern]))  # Use list, since we want to access its content multiple times
        assert matches, "A match expected"
        nrof_matches = len(matches)
        assert nrof_matches == 1, f"One match expected, yet got {nrof_matches}"
        match = matches[0]

        rewriter = ASTRewriter(atu)
        return rewriter, match

    @pytest.mark.skip("TODO: Test fails as prepend of child appears before prepend of parent")
    def test_prepend_child_parent(self) -> None:
        """AI: Verify prepending to the child then the parent nests both insertions in child-before-parent order (currently fails)."""
        rewriter, match = self.setup()
        rewriter.insert_before("4 *", match.expansions["$a"])
        rewriter.insert_before("6 +", match.nodes)
        assert rewriter.apply_to_string() == "x = 6 + 4 * a * b", "Unexpected replacement"
        # TODO: Test fails as prepend of child appears before prepend of parent

    @pytest.mark.skip("TODO: Test fails as prepend of child appears before prepend of parent")
    def test_prepend_parent_child(self) -> None:
        """AI: Verify prepending to the parent then the child nests both insertions in child-before-parent order."""
        rewriter, match = self.setup()
        rewriter.insert_before("6 +", match.nodes)
        rewriter.insert_before("4 *", match.expansions["$a"])
        assert rewriter.apply_to_string() == "x = 6 + 4 * a * b", "Unexpected replacement"

    @pytest.mark.skip("TODO: Test fails as prepend of child appears before prepend of parent")
    def test_append_child_parent(self) -> None:
        """AI: Verify appending to the child then the parent nests both insertions in child-before-parent order."""
        rewriter, match = self.setup()
        rewriter.insert_after("* 4", match.expansions["$b"])
        rewriter.insert_after("+ 6", match.nodes)
        assert rewriter.apply_to_string() == "x = a * b * 4 + 6", "Unexpected replacement"

    @pytest.mark.skip("TODO: Test fails as prepend of child appears before prepend of parent")
    def test_append_parent_child(self) -> None:
        """AI: Verify appending to the parent then the child nests both insertions in child-before-parent order (currently fails)."""
        rewriter, match = self.setup()
        rewriter.insert_after("+ 6", match.nodes)
        rewriter.insert_after("* 4", match.expansions["$b"])
        assert rewriter.apply_to_string() == "x = a * b * 4 + 6", "Unexpected replacement"
        # TODO: Test fails as append of child appears after append of parent


class TestSyntaxAwareAdjacentComposition:
    """Test Class for Syntax Aware Adjacent Compositions.

    In C/C++
    * Consecutive / contiguous nodes - append after first and prepend before second
      See https://github.com/TNO/Renaissance-Experiments/wiki/Transform-%E2%80%90-AST%E2%80%90aware-changes#scenario-combination-of-append-and-prepend-on-consecutive-nodes.

    Note in C/C++ `;` is a terminator that is a part of a statement
         in Python `;` is a separator that can be used to put multiple statements on the same line
    """

    def setup(self, factory: ASTFactory):
        """AI: Build a rewriter and a single match for two adjacent statements 'i++;j++;' against '$stmt1; $stmt2;'."""
        code_text: str = "void f(int i, int j) { i++;j++; }"
        pattern_text: str = " $stmt1; $stmt2; "

        atu = factory.create_from_text(code_text, "test.c")
        pattern = CPatternFactory(factory).create_statements(pattern_text)
        matches = list(find_all([atu], [pattern]))

        assert matches, "A match expected"
        nrof_matches = len(matches)

        assert nrof_matches == 1, f"One match expected, yet got {nrof_matches}"
        match = matches[0]

        rewriter = ASTRewriter(atu)
        return rewriter, match

    @pytest.mark.skip("TODO: implement accordingly")
    def test_first_append_prepend_second(self) -> None:
        """AI: Verify appending after the first statement then prepending before the second nests in source order (not yet implemented)."""
        # setup
        rewriter, match = self.setup(ASTFactory(ClangASTNode))

        # execute
        rewriter.insert_after("++i;", match.expansions["$stmt1"])
        rewriter.insert_before("++j;", match.expansions["$stmt2"])

        # verify
        assert rewriter.apply_to_string() == "void f(int i, int j) { i++;++i;++j;j++; }", "Unexpected replacement"

    @pytest.mark.parametrize(("name", "factory"), Factories.factories)
    @pytest.mark.skip("TODO: implement accordingly")
    def test_prepend_second_first_append(self, name: str, factory: ASTFactory) -> None:
        """AI: Verify prepend-before-second then append-after-first nests in source order, across factories (not yet implemented)."""
        # setup
        rewriter, match = self.setup(factory)

        # execute
        rewriter.insert_before("++j;", match.expansions["$stmt2"])
        rewriter.insert_after("++i;", match.expansions["$stmt1"])

        # verify
        assert rewriter.apply_to_string() == "void f(int i, int j) { i++;++i;++j;j++; }", f"{name}: Unexpected replacement"
