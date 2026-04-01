import sys
from typing import Any

from renaissance.impl.python.python_ast_node import PythonASTNode
from renaissance.impl.python.python_pattern_factory import PythonPatternFactory

import pytest
from hamcrest import assert_that, is_, is_not

from c_cpp.factories import Factories
from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory, MatchFinder, PatternMatch
from renaissance.syntax_tree.ast_rewriter import _RewriteAction, _RewriteActions
from renaissance.syntax_tree.match_finder import find_all, match_pattern
from utils_for_tests import compress, debug_print


class TestCommentLocation:

    @pytest.mark.parametrize(
        "_, start_offset, stop_offset, content, expected",
        [
            (
                "single_line_comment",
                0,
                50,
                b"Some code // this is a comment\nMore code",
                (10, 30),
            ),
            (
                "double_line_comment",
                0,
                50,
                b"Some code// one\n // two\nMore code",
                (17, 23),
            ),
            (
                "block_comment",
                0,
                50,
                b"Some code /* this is a block comment */ More code",
                (10, 39),
            ),
            (
                "hash_comment",
                0,
                50,
                b"Some code # this is a hash comment\nMore code",
                (10, 34),
            ),
            ("no_comment", 0, 50, b"Some code with no comment\nMore code", (-1, -1)),
            (
                "comment_outside_range",
                0,
                10,
                b"Some code // this is a comment\nMore code",
                (-1, -1),
            ),
            (
                "multiple_comments",
                0,
                50,
                b"Some code // first comment\nMore code /* second comment */",
                (10, 26),
            ),
        ],
    )
    def test(
        self,
        _,
        start_offset: int,
        stop_offset: int,
        content: bytes,
        expected: tuple[int, int],
    ):
        result = ASTRewriter._get_comment_location(start_offset, stop_offset, content)
        # converted print but what to do it true???
        # assert_that(result, is_not((-1, -1)), f"first char={content[result[0]:result[1]]}")
        assert_that(expected, is_(result))


class TestRewrites:
    def test_passing_case_in_clang(self):
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

    def test_failing_case(self):
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
        action: Any,
        factory: ASTFactory,
        code: str,
        replacement: str,
        include_whitespace: bool,
        include_comments: bool,
        expected: str,
    ):
        atu = factory.create_from_text(code, "test.cpp")
        pattern_factory = CPatternFactory(factory)
        declaration_pattern = pattern_factory.create_declarations("int a=3;")
        rewriter = ASTRewriter(atu)
        found = match_pattern(atu.children, declaration_pattern)

        for match in found:  # .map(lambda m: m.nodes).to_iterable():
            nodes = match.nodes
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

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):

        reemove = lambda s, _, n, ws, cm: ASTRewriter.remove(s, n, ws, cm)
        self.do_test(
            reemove,
            factory,
            code,
            "int aa=4;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestReplace(TestRewrites):

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):
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

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):
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

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):
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

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):
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

    @pytest.mark.parametrize(
        "name, factory, code, include_whitespace, include_comments, expected",
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
                ]
            )
        ),
    )
    def test(
        self,
        name: str,
        factory: ASTFactory,
        code: str,
        include_whitespace: Any,
        include_comments: Any,
        expected: Any,
    ):
        self.do_test(
            ASTRewriter.insert_after,
            factory,
            code,
            "int aa=4;\nint bb=5;",
            include_whitespace,
            include_comments,
            expected,
        )


class TestComposeReplacement:

    @pytest.mark.parametrize(
        "_, factory, statements, extra_declarations, replacement",
        Factories.extend(
            [
                (
                    "if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}",
                    [],
                    {"$$before; b = ($exp) ? $d1:$d2; $$after;": "int a=1;int b=2;int c=3;int d=4;void f(){c++;b=(a==1)?2:3;d++;}"},
                ),
            ]
        ),
    )
    def test_args(
        self,
        _: Any,
        factory: ASTFactory,
        statements: Any,
        extra_declarations: Any,
        replacement: Any,
    ):
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
        matches = (match for match in match_pattern([atu], stmt_nodes) if match.nodes[0].is_part_of_translation_unit())

        for match, exp in zip(matches, replacement.items()):
            rewriter = ASTRewriter(match.nodes[0].root)
            org, expected = exp
            rewriter.replace(org, match)
            actual = rewriter.apply_to_string()
            assert_that(compress(expected), is_(compress(actual)))
    def test_get_node_in_match_pattern(self,mocker):
        node = mocker.Mock()
        reference = mocker.Mock()
        node.referenced_by = [reference, reference]
        reference.node = node
        pattern_match = PatternMatch([node, node, node], {}, [])
        n = _RewriteAction._get_nodes([pattern_match])[0]
        assert_that(n, is_(node))
    
    
    
    @pytest.mark.skip("fail on empty nodes")
    def test_get_node_in_match_pattern(self):
        it = _RewriteActions([], sys.getfilesystemencoding(), True)
        text = getattr(it, "_RewriteActions__get_texts")([])
        assert_that(text, is_("node"))
    
    
    
    def test_get_text_from_rewrite(self,mocker):
        node = mocker.Mock()
        node.root = node
        node.binary_file_content = lambda: b"int x =0;"
        node.offset = 0
        node.extended_end_offset = 8
        node.text = "int x =0"
    
        it = _RewriteActions(node, sys.getfilesystemencoding(), True)
        text = getattr(it, "_RewriteActions__get_texts")([node])
        assert_that(text, is_("int x =0"))
    
    
class TestSyntaxAwareComposition:
    def setup(self) -> tuple[ASTRewriter, PatternMatch] :
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text("x = a * b", "temp.py")
        rewriter = ASTRewriter(atu)
        pattern = PythonPatternFactory(factory).create_expression("$a * $b")
        matches = list(find_all([atu], [pattern]))      # Use list, since we want to access its content multiple times
        assert matches, "A match expected"
        nrof_matches = len(matches)
        assert 1 == nrof_matches, f"One match expected, yet got {nrof_matches}"
        match = matches[0]
        return rewriter, match

    def test_prepend_child_parent(self):
        rewriter, match = self.setup()
        rewriter.insert_before("4 *", match.expansions['$a'])
        rewriter.insert_before("6 +", match.nodes)
        assert "x = 6 + 4 * a * b" == rewriter.apply_to_string(), "Unexpected replacement"
  
    def test_prepend_parent_child(self):
        rewriter, match = self.setup()
        rewriter.insert_before("4 *", match.nodes)
        rewriter.insert_before("6 +", match.expansions['$a'])
        assert "x = 6 + 4 * a * b" == rewriter.apply_to_string(), "Unexpected replacement"
  
    def test_append_child_parent(self):
        rewriter, match = self.setup()
        rewriter.insert_after("* 4", match.expansions['$b'])
        rewriter.insert_after("+ 6", match.nodes)
        assert "x = a * b * 4 + 6" == rewriter.apply_to_string(), "Unexpected replacement"
  
    def test_append_parent_child(self):
        rewriter, match = self.setup()
        rewriter.insert_after("* 4", match.nodes)
        rewriter.insert_after("+ 6", match.expansions['$b'])
        assert "x = a * b * 4 + 6" == rewriter.apply_to_string(), "Unexpected replacement"
  




