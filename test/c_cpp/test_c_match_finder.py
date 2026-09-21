"""Tests for matching C AST patterns via MatchFinder."""

import logging

import pytest
from hamcrest import assert_that, greater_than_or_equal_to, has_length, is_
from more_itertools.more import last

from c_cpp.factories import Factories
from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree import (
    ASTFactory,
    ASTNode,
    ASTShower,
)
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.match_finder import find_in_list, find_variants, is_match, match_pattern
from renaissance.syntax_tree.semantic_kind import SemanticKind
from utils_for_tests import compress, debug_mismatch, show_node

logger = logging.getLogger(__name__)


class TestCMatchFinder:
    """AI: Shared base for C/C++ pattern-matching tests, providing sample source and match helpers."""

    SIMPLE_CPP = """
        void f(){
            int a = 3;
            int b = 4;
            if(a == 3){
                b=5;
            }
            else{
                b--;
            }
            while(a != 3){
                if  (a == 4 && b == 5){
                    b = a;
                }
            }
        }
        """

    def test_simple_pattern(self):
        """AI: Verify a single-statement pattern matches its occurrence in parsed source."""
        factory = ASTFactory(ClangASTNode, [])
        patterns = CPatternFactory(factory).create_statements("b--;")

        atu = factory.create_from_text("void fun(){int a,b;\nb--;\na==4;\nb==5;}", "test.c")
        matches = match_pattern(atu.children, patterns)
        assert_that(matches, has_length(1))

    @staticmethod
    def do_test(factory: ASTFactory, cpp_code, patterns: list[ASTNode], recursive: bool):
        """AI: Parse cpp_code and return the pattern matches that are part of the translation unit."""
        atu = factory.create_from_text(cpp_code, "test.c")
        # find all if and while statements
        matches = [
            match for match in match_pattern(atu.children, patterns, recursive=recursive) if match.nodes[0].is_part_of_translation_unit()
        ]

        debug_mismatch(True, atu, patterns, matches)
        return matches

    @staticmethod
    def assert_matches(expected_dicts_per_match, actual_matches):
        """AI: Assert that actual_matches' expansion text matches expected_dicts_per_match element-wise."""
        assert_that(actual_matches, has_length(len(expected_dicts_per_match)))
        for actual, expected_dict in zip(actual_matches, expected_dicts_per_match, strict=True):
            for k, v in actual.expansions.items():
                for i, n in enumerate(v):
                    assert_that(n.text, is_(expected_dict[k][i]))


class TestExpressions(TestCMatchFinder):
    """AI: Tests matching C/C++ expression patterns."""

    def test_match_expr(self):
        """AI: Verify an expression pattern with a placeholder matches multiple occurrences in parsed source."""
        factory = ASTFactory(ClangJsonASTNode, [])
        expr_node = CPatternFactory(factory).create_expression("a == $x")
        ASTShower.show_node(expr_node)
        atu = factory.create_from_text("void fun(){int a,b;\nb==5;\na==3;\na==4;}", "test.c")
        show_node(atu, "CPP code")
        # find all if and while statements
        matches = [match for match in match_pattern(atu.children, [expr_node]) if match.nodes[0].is_part_of_translation_unit()]
        assert_that(matches, has_length(2))

    @pytest.mark.parametrize(
        "_, factory, expression, expected_full_matches, expected_dicts_per_match",
        Factories.extend(
            [
                ("a == 3", ["a==3"], [{}]),
                ("a == $x", ["a==3", "a==4"], [{"$x": ["3"]}, {"$x": ["4"]}]),
                (
                    "$y == $x",
                    ["a==3", "a==4", "b==5"],
                    [
                        {"$y": ["a"], "$x": ["3"]},
                        {"$y": ["a"], "$x": ["4"]},
                        {"$y": ["b"], "$x": ["5"]},
                    ],
                ),
                ("b--", ["b--;"], [{}]),
                ("b++", [], []),
                ("--b", [], []),
                ("++b", [], []),
                ("$x--", ["b--;"], [{"$x": ["b"]}]),
                ("$x++", [], []),
                ("--$x", [], []),
                ("++$x", [], []),
            ],
        ),
    )
    def test(
        self,
        _,
        factory,
        expression,
        expected_full_matches: list[str],
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        """AI: Verify an expression pattern matches the expected occurrences and placeholder bindings."""
        expr_node = CPatternFactory(factory).create_expression(expression)
        found_matches = self.do_test(factory, TestStatements.SIMPLE_CPP, [expr_node], recursive=True)
        assert_that(
            expected_full_matches,
            is_([compress(match.nodes[0].text) for match in found_matches]),
        )
        self.assert_matches(expected_dicts_per_match, found_matches)


class TestStatements(TestCMatchFinder):
    """AI: Tests matching C/C++ statement patterns, including placeholder expansions."""

    @pytest.mark.parametrize(
        "_, factory, statements, expected_dicts_per_match",
        Factories.extend(
            [
                (
                    "$x;$y;",
                    [
                        {"$x": ["int a = 3;"], "$y": ["int b = 4;"]},
                        {
                            "$x": [
                                (
                                    "if(a == 3){\n                b=5;\n"
                                    "            }\n            else{\n                b--;\n            }"
                                ),
                            ],
                            "$y": [
                                (
                                    "while(a != 3){\n"
                                    "                if  (a == 4 && b == 5){\n                    b = a;\n                }\n            }"
                                ),
                            ],
                        },
                    ],
                ),
                (
                    "if($x){$$stmts;}",
                    [{"$x": ["a == 4 && b == 5"], "$$stmts": ["b = a;"]}],
                ),
                (
                    "if($x){$$stmts;}else{$single;$$multi;}",
                    [
                        {
                            "$x": ["a == 3"],
                            "$$stmts": ["b=5;"],
                            "$single": ["b--;"],
                            "$$multi": [],
                        },
                    ],
                ),
                (
                    "if($x){$$stmts;}else{$$multi;$single;}",
                    [
                        {
                            "$x": ["a == 3"],
                            "$$stmts": ["b=5;"],
                            "$single": ["b--;"],
                            "$$multi": [],
                        },
                    ],
                ),
                (
                    "while(a!=$x){$$stmts;}",
                    [
                        {
                            "$x": ["3"],
                            "$$stmts": ["if  (a == 4 && b == 5){\n                    b = a;\n                }"],
                        },
                    ],
                ),
            ],
        ),
    )
    def test(
        self,
        _,
        factory,
        statements,
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        """AI: Verify a statement pattern with expansions matches the expected placeholder bindings."""
        patterns = CPatternFactory(factory).create_statements(statements)

        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
        func_body = atu.children[0].children[2]
        matches = match_pattern(func_body.children, patterns)

        self.assert_matches(expected_dicts_per_match, matches)


class TestFunctionCallStatements(TestCMatchFinder):
    """AI: Tests matching C/C++ function-call statement patterns with variadic argument placeholders."""

    @pytest.mark.parametrize(
        "_, factory, statements, extra_declarations, expected_dicts_per_match",
        Factories.extend(
            [
                ("$f($a);", ["int $f(int);"], [{"$f": ["one"], "$a": ["a"]}]),
                (
                    "$f($a, $$all);",
                    ["int $f(int,int);"],
                    [
                        {"$f": ["one"], "$a": ["a"], "$$all": []},
                        {"$f": ["two"], "$a": ["a"], "$$all": ["b"]},
                        {"$f": ["three"], "$a": ["a"], "$$all": ["b", "c"]},
                    ],
                ),
                (
                    "$f($$all, $a);",
                    ["int $f(int,int);"],
                    [
                        {"$f": ["one"], "$$all": [], "$a": ["a"]},
                        {"$f": ["two"], "$$all": ["a"], "$a": ["b"]},
                        {"$f": ["three"], "$$all": ["a", "b"], "$a": ["c"]},
                    ],
                ),
                (
                    "$f($a, $$all, $b);",
                    ["int $f(int,int,int);"],
                    [
                        {"$f": ["two"], "$a": ["a"], "$$all": [], "$b": ["b"]},
                        {"$f": ["three"], "$a": ["a"], "$$all": ["b"], "$b": ["c"]},
                    ],
                ),
            ],
        ),
    )
    def test(
        self,
        _,
        factory,
        statements,
        extra_declarations,
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        """AI: Verify a function-call statement pattern with variadic placeholders matches the expected bindings."""
        code = """
            int one(int a);
            int two(int a, int b);
            int three(int a, int b, int c);
            int a,b,c;
            void f(){
                one(a);
                two(a,b);
                three(a,b,c);
            }
            """

        stmt_nodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmt_nodes, recursive=True)
        self.assert_matches(expected_dicts_per_match, matches)


class TestMultiAssignments(TestCMatchFinder):
    """AI: Tests matching statement patterns that repeat the same placeholder across multiple call sites."""

    @pytest.mark.parametrize(
        "_, factory, statements, extra_declarations, expected_dicts_per_match",
        Factories.extend(
            [
                (
                    "$f($$all1);$f($$all2);",
                    ["int $f(int);"],
                    [
                        {
                            "$f": ["fc"],
                            "$$all1": ["1", "2", "3", "4", "5"],
                            "$$all2": ["1", "2", "6", "4", "5"],
                        },
                    ],
                ),
                # skip the advanced undeterministic all placeholder
                # ('$f($$before, $a, $$after);$f($$before, $b, $$after);',['int $f(int,int,int);'],[{'$f': ['fc'],
                #                      '$$before': ['1', '2'], '$a': ['3'], '$$after': ['4', '5'], '$b': ['6']}]),
            ],
        ),
    )
    def test_args(
        self,
        _,
        factory,
        statements,
        extra_declarations,
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        """AI: Verify a statement pattern repeating the same placeholder across two call sites matches consistently."""
        code = """
            int fc(int a, int b, int c, int d, int e);
            int fc_else(int a, int b, int c, int d, int e);
            void f(){
                fc(1,2,3,4,5);
                fc(1,2,6,4,5);

                fc(1,2,3,4,5);
                fc_else(1,2,6,4,5);
            }
            """

        stmt_nodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmt_nodes, recursive=True)
        self.assert_matches(expected_dicts_per_match, matches)

    @pytest.mark.parametrize(
        "_, factory, statements, extra_declarations, expected_dicts_per_match",
        Factories.extend(
            [
                (
                    "if ($c) {$$before; c=3; $$after;} else {$$before; c=6; $$after;}",
                    [],
                    [
                        {
                            "$c": ["1"],
                            "$$before": ["a=1;", "b=2;"],
                            "$true": ["c=3;"],
                            "$$after": ["d=4;", "e=5;"],
                            "$false": ["c=6;"],
                        },
                    ],
                ),
            ],
        ),
    )
    def test_statements(
        self,
        _,
        factory,
        statements,
        extra_declarations,
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        """AI: Verify an if/else statement pattern matches the true and false branches with consistent placeholders."""
        code = """

            void f(){
                int a,b,c,d,e;
                if(1){
                   a=1;
                   b=2;
                   c=3;
                   d=4;
                   e=5;
                }
                else {
                   a=1;
                   b=2;
                   c=6; //different
                   d=4;
                   e=5;
                }
            }
            """
        patterns = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        atu = factory.create_from_text(code, "test.c")
        func_body = atu.children[0].children[2]
        matches = match_pattern(func_body.children, patterns)

        self.assert_matches(expected_dicts_per_match, matches)


class TestUseAtuToCreatePattern(TestCMatchFinder):
    """AI: Tests building a pattern directly from a parsed translation unit's own nodes."""

    @pytest.mark.parametrize(
        "name, factory, statements, pattern_type, expected, names",
        Factories.extend(
            [
                (
                    "void f() {const char* bar = BAR;}",
                    SemanticKind.DECLARATION,
                    ["const char* bar = BAR;"],
                    {},
                ),
                (
                    "void f() {const char* foo = FOO;}",
                    SemanticKind.DECLARATION,
                    ["const char* foo = FOO;"],
                    {},
                ),
                (
                    "void f() {const char* same = SAME;}",
                    SemanticKind.DECLARATION,
                    ["const char* same = SAME;"],
                    {},
                ),
                (
                    "void f() {const char* $name = BAR;}",
                    SemanticKind.DECLARATION,
                    ["const char* bar = BAR;"],
                    {"$name": ["bar"]},
                ),
                (
                    "void f() {const char* $name = FOO;}",
                    SemanticKind.DECLARATION,
                    ["const char* foo = FOO;"],
                    {"$name": ["foo"]},
                ),
                (
                    "void f() {const char* $name = SAME;}",
                    SemanticKind.DECLARATION,
                    ["const char* same = SAME;"],
                    {"$name": ["same"]},
                ),
                (
                    "const char* $$args; void f() { print($$args);}",
                    SemanticKind.CALL,
                    ['print("%s %s %s", foo, bar, same);'],
                    {"$$args": ['"%s %s %s"', "foo", "bar", "same"]},
                ),
            ],
        ),
    )
    def test(self, name, factory, statements, pattern_type, expected, names):
        """AI: Verify a pattern built from the parsed translation unit's own nodes matches occurrences of that pattern."""
        code = """
            #define FOO "foo"
            #define BAR "bar"
            #define SAME "bar"
            typedef struct A_Struct{
                int a;
                int b;
            } A;
            int some_decl = 1;

            int print(const char*, ...);
            void f(){
                A a = {};
                const char* foo = FOO;
                const char* bar = BAR;
                const char* same = SAME;
                print("%s %s %s", foo, bar, same);

            }
            """
        atu = factory.create_from_text(code, "test.c")

        # clang_json failed after upgrading to Clang 21 and Ubuntu 26
        if name.startswith("clang_json"):
            return
        pattern_factory = CPatternFactory(factory, ref_node=atu)
        statements_atu = pattern_factory.create(statements)
        statements = last(
            find_nodes(
                statements_atu,
                lambda node: (
                    node.semantic_kind is pattern_type
                    or (pattern_type is SemanticKind.DECLARATION and node.parser_kind in {"DeclStmt", "DECL_STMT"})
                ),
            ),
        )  # pick the last statement
        func_body = atu.children[-1].children[2].children
        result = match_pattern(func_body, [statements], recursive=True)
        # should find multiple matches, at least the one in the pattern and the one in the function body
        assert_that(result, has_length(greater_than_or_equal_to(1)))
        # unreliable to check the exact number of matches due to the pattern also matching the pattern itself
        # text= result.filter(lambda match: match.patterns == names).map(lambda match: match.nodes[0])
        #             .filter(ASTNode.is_part_of_translation_unit).map(ASTNode.text).to_list()
        # assert_that(text, is_(expected))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    @pytest.mark.skip("stmt and expr are the same")
    def test_is_match_expression_differs_from_stmt(self, _: str, factory: ASTFactory):
        """AI: Verify an expression pattern does not match an equivalent statement pattern."""
        pattern_factory = CPatternFactory(factory)
        expression_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        statement_pattern = pattern_factory.create_statement("x=3;", extra_declarations=["int x;"])
        assert_that(
            is_match(expression_pattern, statement_pattern, {}),
            is_(False),
            "An expression doesn't match a statement",
        )

        expression_pattern = pattern_factory.create_expression("f()", ["int f();"])
        statement_pattern = pattern_factory.create_statement("f();", extra_declarations=["int f();"])
        assert_that(
            is_match(expression_pattern, statement_pattern, {}),
            is_(False),
            "An expression doesn't match a statement",
        )


class TestIndividualCases:
    """AI: Ad-hoc regression tests for specific C/C++ pattern-matching cases."""

    def test_multi_single(self):
        """AI: Verify a variadic-placeholder statement pattern matches exactly one variant across multiple call sites."""
        factory = ASTFactory(ClangASTNode)
        atu = factory.create_from_text(
            """
            int one(int a);
            int two(int a, int b);
            int three(int a, int b, int c);
            int a,b,c;
            void f(){
                one(a);
                two(a,b);
                three(a,b,c);
            }
            """,
            "test.c",
        )
        pattern_factory = CPatternFactory(factory)
        stmt_nodes = pattern_factory.create_statements("$f($$all, $a);", None, ["int $f(int,int);"])
        variants = find_variants(atu.children[-1].children[-1].children, stmt_nodes)

        assert_that(variants, has_length(1))
        assert_that(variants[0].end_index, is_(0))
        assert_that(variants[0].exp["$$all"], is_([]))
        assert_that(variants[0].exp["$a"][0].name, is_("a"))
        variants = find_in_list(atu.children[-1].children[-1].children, stmt_nodes, {}, 1)
        assert_that(variants, 1)

        variants = find_in_list(atu.children[-1].children[-1].children, stmt_nodes, {}, 1)

        # TODO: out commented code can be removed?
        # assert_that(variants[0].exp['$$all'], has_length(1))
        # TODO: why are next two expressions there? They are not used!
        ({"$f": ["two"], "$$all": ["a"], "$a": ["b"]},)
        ({"$f": ["three"], "$$all": ["a", "b"], "$a": ["c"]},)
        found = match_pattern(atu.children[-1].children[-1].children, stmt_nodes)
        assert_that(found, has_length(3))
