# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the ASTRewriter: removing, replacing and inserting code around matched nodes."""

from collections.abc import Callable, Sequence

import pytest
from hamcrest import assert_that, has_length, is_

from renaissance.core.match import match_pattern
from renaissance.core.model import ASTFactory
from renaissance.core.rewrite import ASTRewriter, Rewritable
from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from test.unit.shared.factories import Factories
from test.unit.shared.utils_for_tests import debug_print


class TestRewrites:
    """AI: Base class with shared helpers for ASTRewriter rewrite-action tests."""

    def test_passing_case_in_clang(self) -> None:
        """AI: Verify insert_before places replacement text between two adjacent comments in a C declaration."""
        # action: Callable[[ASTRewriter, str, Sequence[ASTNode], bool, bool], None],
        # factory: ASTFactory,code: str, replacement: str, include_whitespace: bool, include_comments: bool, expected: str):
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text("void f() { /* c1 */ /* c2 */ int a=3;\n}", "test.cpp")
        pattern_factory = CPatternFactory(factory)
        declaration_pattern = pattern_factory.create_declarations("int a=3;")
        found = match_pattern(atu.children, declaration_pattern)

        rewriter = ASTRewriter(atu)
        for match in found:  # .map(lambda m: m.nodes).to_iterable():
            nodes = match.nodes
            rewriter.insert_before("int b=4;int c=5;", nodes, True, True)
        assert_that(
            rewriter.apply_to_string(),
            is_("void f() { /* c1 */ int b=4;int c=5;\n /* c2 */ int a=3;\n}"),
        )

    @staticmethod
    def do_test(
        action: Callable[[ASTRewriter, str, Sequence[Rewritable], bool, bool], None],
        factory: ASTFactory,
        code: str,
        replacement: str,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply the given rewrite action to the matched declaration and assert the resulting text matches expected."""
        atu = factory.create_from_text(code, "test.cpp")
        pattern_factory = CPatternFactory(factory)
        declaration_pattern = pattern_factory.create_declarations("int a=3;")
        rewriter = ASTRewriter(atu)
        found = match_pattern(atu.children, declaration_pattern)

        for match in found:  # .map(lambda m: m.nodes).to_iterable():
            nodes: Sequence[Rewritable] = match.nodes
            action(rewriter, replacement, nodes, include_whitespace, include_comments)
        expected_result = factory.create_from_text(expected, "test.cpp")
        actual = rewriter.apply_to_string()
        actual_result = factory.create_from_text(rewriter.apply_to_string(), "test.cpp")
        debug_print(
            actual,
            actual_result,
            atu,
            code,
            expected,
            expected_result,
            include_comments,
            include_whitespace,
        )

        assert_that(actual, is_(expected))


class TestRemove(TestRewrites):
    """AI: Tests for ASTRewriter.remove."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    ("void f() { /* c1 */ int a=3;\n}", True, True, "void f() {\n}"),
                    (
                        "void f() { int x=2; //x cmt\n  int a=3;\n}",
                        True,
                        True,
                        "void f() { int x=2; //x cmt\n}",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.remove to the matched declaration and assert the resulting text matches expected."""
        self.do_test(
            # remove takes no replacement text, so the action signature's second parameter is dropped here.
            lambda rewriter, _, nodes, whitespace, comments: ASTRewriter.remove(rewriter, nodes, whitespace, comments),
            factory,
            code,
            "int aa=4;",
            include_whitespace,
            include_comments,
            expected,
        )

    def test_remove_last_node_at_eof_without_trailing_newline(self) -> None:
        """AI: Removing a final node at EOF should not crash and should keep surrounding content intact."""
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text("import DDXA\nfrom TAUT import TestDoubles", "test.py")
        pattern = PythonPatternFactory(factory).create_statements("from TAUT import TestDoubles")
        matches = list(match_pattern(atu.children, pattern))

        assert_that(matches, has_length(1))

        rewriter = ASTRewriter(atu)
        rewriter.remove(matches[0].nodes, False, False)

        assert_that(rewriter.apply_to_string(), is_("import DDXA"))


class TestReplace(TestRewrites):
    """AI: Tests for ASTRewriter.replace."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    (
                        "void f() { /* c1 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n}",
                    ),
                    (
                        "void f() { /* c1 */ /* c2 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ int aa=4;\n}",
                    ),
                    (
                        "void f() { // c1\n int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n}",
                    ),
                    (
                        "void f() { // c1\n //c2\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n int aa=4;\n}",
                    ),
                    (
                        "void f() { int a=3;    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n}",
                    ),
                    (
                        "void f() { int a=3; //c1    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n}",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "void f() { int aa=4; }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "void f() { int aa=4; }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* out scope */ void f() { int aa=4; }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* out scope */ void f() { int aa=4; }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* out scope */ void f() { int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        False,
                        "void f() { int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int aa=4; /*c1    \n */ }",
                    ),
                    # siblings with comments
                    (
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /* c1 */ int aa=4;\n int b=4; }",
                    ),
                    (
                        "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { //cx\nint x=2; //ca\n int aa=4;\n int b=4;//cb \n}",
                    ),
                    (
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /*ca*/ int aa=4; int b=4; }",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.replace to the matched declaration and assert the resulting text matches expected."""
        self.do_test(
            ASTRewriter.replace,
            factory,
            code,
            "int aa=4;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestInsertBeforeSingleLine(TestRewrites):
    """AI: Tests for ASTRewriter.insert_before with a single-line insertion."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* out scope */ void f() { int aa=4;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* out scope */ void f() { int aa=4;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* out scope */ void f() { int aa=4; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { /* c1 */ /* c2 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ int aa=4;\n /* c2 */ int a=3;\n}",
                    ),
                    (
                        "void f() { /* c1 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n /* c1 */ int a=3;\n}",
                    ),
                    (
                        "void f() { // c1\n //c2\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n int aa=4;\n //c2\n int a=3;\n}",
                    ),
                    (
                        "void f() { // c1\n int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n // c1\n int a=3;\n}",
                    ),
                    (
                        "void f() { //cx\n int x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { //cx\n int x=2; //ca\n int aa=4;\n int a=3; //caa\n int b=4;//cb \n}",
                    ),
                    (
                        "void f() { int a=3;    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int a=3;    \n}",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int aa=4;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "void f() { int aa=4;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        False,
                        "void f() { int aa=4; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "void f() { int aa=4; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; //c1    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int a=3; //c1    \n}",
                    ),
                    (
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /*ca*/ int aa=4; int a=3; /*caa \n nl*/ int b=4; }",
                    ),
                    (
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /* c1 */ int aa=4;\n int a=3; //c2\n int b=4; }",
                    ),
                    (
                        "void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { int x=2; //c1\n int aa=4;\n int a=3; //caa\n int b=4;//cb \n}",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.insert_before with a single-line insertion and assert the resulting text matches expected."""
        self.do_test(
            ASTRewriter.insert_before,
            factory,
            code,
            "int aa=4;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestInsertBeforeMultiLine(TestRewrites):
    """AI: Tests for ASTRewriter.insert_before with a multi-line insertion."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* out scope */ void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* out scope */ void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* out scope */ void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;  int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { /* c1 */ /* c2 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ int aa=4;\n int bb=5;\n /* c2 */ int a=3;\n}",
                    ),
                    (
                        "void f() { /* c1 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int bb=5;\n /* c1 */ int a=3;\n}",
                    ),
                    (
                        "void f() { // c1\n //c2\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n int aa=4;\n int bb=5;\n //c2\n int a=3;\n}",
                    ),
                    (
                        "void f() { // c1\n int a=3;\n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int bb=5;\n // c1\n int a=3;\n}",
                    ),
                    (
                        "void f() { //cx\n int x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { //cx\n int x=2; //ca\n int aa=4;\n int bb=5;\n int a=3; //caa\n int b=4;//cb \n}",
                    ),
                    (
                        "void f() { int a=3;    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int bb=5;\n int a=3;    \n}",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        False,
                        "void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; //c1    \n}",
                        True,
                        True,
                        "void f() { int aa=4;\n int bb=5;\n int a=3; //c1    \n}",
                    ),
                    (
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /*ca*/ int aa=4;\n int bb=5; int a=3; /*caa \n nl*/ int b=4; }",
                    ),
                    (
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /* c1 */ int aa=4;\n int bb=5;\n int a=3; //c2\n int b=4; }",
                    ),
                    (
                        "void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { int x=2; //c1\n int aa=4;\n int bb=5;\n int a=3; //caa\n int b=4;//cb \n}",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.insert_before with a multi-line insertion and assert the resulting text matches expected."""
        self.do_test(
            ASTRewriter.insert_before,
            factory,
            code,
            "int aa=4;\nint bb=5;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestInsertAfterSingleLine(TestRewrites):
    """AI: Tests for ASTRewriter.insert_after with a single-line insertion."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* out scope */ void f() { int a=3;int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* out scope */ void f() { int a=3; /*c1    \n */int aa=4; }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* out scope */ void f() { int a=3; /*c1    \n */ int aa=4; }",
                    ),
                    (
                        "void f() { /* c1 */ /* c2 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ /* c2 */ int a=3;\n int aa=4;\n}",
                    ),
                    (
                        "void f() { /* c1 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ int a=3;\n int aa=4;\n}",
                    ),
                    (
                        "void f() { // c1\n //c2\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n //c2\n int a=3;\n int aa=4;\n}",
                    ),
                    (
                        "void f() { // c1\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n int a=3;\n int aa=4;\n}",
                    ),
                    (
                        "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int aa=4;\n int b=4;//cb \n}",
                    ),
                    (
                        "void f() { int a=3;    \n}",
                        True,
                        True,
                        "void f() { int a=3;    \n int aa=4;\n}",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int a=3;int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "void f() { int a=3; /*c1    \n */int aa=4; }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        False,
                        "void f() { int a=3; int aa=4; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "void f() { int a=3; /*c1    \n */ int aa=4; }",
                    ),
                    (
                        "void f() { int a=3; //c1    \n}",
                        True,
                        True,
                        "void f() { int a=3; //c1    \n int aa=4;\n}",
                    ),
                    (
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int aa=4; int b=4; }",
                    ),
                    (
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int aa=4;\n int b=4; }",
                    ),
                    (
                        "void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { int x=2; //c1\n int a=3; //caa\n int aa=4;\n int b=4;//cb \n}",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.insert_after with a single-line insertion and assert the resulting text matches expected."""
        self.do_test(
            ASTRewriter.insert_after,
            factory,
            code,
            "int aa=4;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestInsertAfterMultiLine(TestRewrites):
    """AI: Tests for ASTRewriter.insert_after with a multi-line insertion."""

    @pytest.mark.parametrize(
        ("name", "factory", "code", "include_whitespace", "include_comments", "expected"),
        list(
            Factories.extend(
                [
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* indent 2 */ void f() {\n  int a=3;int aa=4;\n  int bb=5; /*c1    \n */ }",
                    ),
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */int aa=4;\n  int bb=5; }",
                    ),
                    (
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */  int aa=4;\n  int bb=5; }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "/* out scope */ void f() { int a=3;int aa=4;\n int bb=5; /*c1    \n */ }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "/* out scope */ void f() { int a=3; /*c1    \n */int aa=4;\n int bb=5; }",
                    ),
                    (
                        "/* out scope */ void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "/* out scope */ void f() { int a=3; /*c1    \n */ int aa=4;\n int bb=5; }",
                    ),
                    (
                        "void f() { /* c1 */ /* c2 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ /* c2 */ int a=3;\n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { /* c1 */ int a=3;\n}",
                        True,
                        True,
                        "void f() { /* c1 */ int a=3;\n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { // c1\n //c2\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n //c2\n int a=3;\n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { // c1\n int a=3;\n}",
                        True,
                        True,
                        "void f() { // c1\n int a=3;\n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int aa=4;\n int bb=5;\n int b=4;//cb \n}",
                    ),
                    (
                        "void f() { int a=3;    \n}",
                        True,
                        True,
                        "void f() { int a=3;    \n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        False,
                        "void f() { int a=3;int aa=4;\n int bb=5; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        False,
                        True,
                        "void f() { int a=3; /*c1    \n */int aa=4;\n int bb=5; }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        False,
                        "void f() { int a=3; int aa=4;\n int bb=5; /*c1    \n */ }",
                    ),
                    (
                        "void f() { int a=3; /*c1    \n */ }",
                        True,
                        True,
                        "void f() { int a=3; /*c1    \n */ int aa=4;\n int bb=5; }",
                    ),
                    (
                        "void f() { int a=3; //c1    \n}",
                        True,
                        True,
                        "void f() { int a=3; //c1    \n int aa=4;\n int bb=5;\n}",
                    ),
                    (
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int aa=4;\n int bb=5; int b=4; }",
                    ),
                    (
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }",
                        True,
                        True,
                        "void f() { int x=2; /* c1 */ int a=3; //c2\n int aa=4;\n int bb=5;\n int b=4; }",
                    ),
                    (
                        "void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}",
                        True,
                        True,
                        "void f() { int x=2; //c1\n int a=3; //caa\n int aa=4;\n int bb=5;\n int b=4;//cb \n}",
                    ),
                ],
            ),
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        *,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ) -> None:
        """AI: Apply ASTRewriter.insert_after with a multi-line insertion and assert the resulting text matches expected."""
        self.do_test(
            ASTRewriter.insert_after,
            factory,
            code,
            "int aa=4;\nint bb=5;",
            include_whitespace,
            include_comments,
            expected,
        )
