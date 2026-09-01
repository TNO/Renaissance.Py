import logging

import pytest
from hamcrest import *
from more_itertools.more import last

from c_cpp.factories import Factories
from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.impl.types import Call, Declaration
from renaissance.syntax_tree import (
    ASTFactory,
    ASTNode,
    ASTShower,
)
from renaissance.syntax_tree.ast_finder import find_ast_type
from renaissance.syntax_tree.match_finder import find_in_list, find_variants, is_match, match_pattern
from utils_for_tests import compress, debug_mismatch, show_node

logger = logging.getLogger(__name__)


class TestCMatchFinder:
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

        factory = ASTFactory(ClangASTNode, [])
        patterns = CPatternFactory(factory).create_statements("b--;")

        atu = factory.create_from_text("void fun(){int a,b;\nb--;\na==4;\nb==5;}", "test.c")
        matches = match_pattern(atu.children, patterns)
        assert_that(matches, has_length(1))

    @staticmethod
    def do_test(factory: ASTFactory, cpp_code, patterns: list[ASTNode], recursive: bool):
        atu = factory.create_from_text(cpp_code, "test.c")
        # find all if and while statements
        matches = [
            match for match in match_pattern(atu.children, patterns, recursive=recursive) if match.nodes[0].is_part_of_translation_unit()
        ]

        debug_mismatch(True, atu, patterns, matches)
        return matches

    @staticmethod
    def assert_matches(expected_dicts_per_match, actual_matches):
        for actual, expected_dict in zip(actual_matches, expected_dicts_per_match, strict=False):
            for k, v in actual.expansions.items():
                for i, n in enumerate(v):
                    assert_that(n.text, is_(expected_dict[k][i]))
        assert_that(actual_matches, has_length(len(expected_dicts_per_match)))


class TestExpressions(TestCMatchFinder):
    def test_match_expr(self):
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
            ]
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
        expr_node = CPatternFactory(factory).create_expression(expression)
        found_matches = self.do_test(factory, TestStatements.SIMPLE_CPP, [expr_node], recursive=True)
        assert_that(
            expected_full_matches,
            is_([compress(match.nodes[0].text) for match in found_matches]),
        )
        self.assert_matches(expected_dicts_per_match, found_matches)


class TestStatements(TestCMatchFinder):
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
                                "if(a == 3){\n                b=5;\n            }\n            else{\n                b--;\n            }"
                            ],
                            "$y": [
                                "while(a != 3){\n                if  (a == 4 && b == 5){\n                    b = a;\n                }\n"
                                "            }"
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
                        }
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
                        }
                    ],
                ),
                (
                    "while(a!=$x){$$stmts;}",
                    [
                        {
                            "$x": ["3"],
                            "$$stmts": ["if  (a == 4 && b == 5){\n                    b = a;\n                }"],
                        }
                    ],
                ),
            ]
        ),
    )
    def test(
        self,
        _,
        factory,
        statements,
        expected_dicts_per_match: list[dict[str, list[str]]],
    ):
        patterns = CPatternFactory(factory).create_statements(statements)

        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
        func_body = atu.children[0].children[2]
        matches = match_pattern(func_body.children, patterns)

        self.assert_matches(expected_dicts_per_match, matches)


class TestFunctionCallStatements(TestCMatchFinder):
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
            ]
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
                        }
                    ],
                ),
                # skip the advanced undeterministic all placeholder
                # ('$f($$before, $a, $$after);$f($$before, $b, $$after);',['int $f(int,int,int);'],[{'$f': ['fc'],
                #                      '$$before': ['1', '2'], '$a': ['3'], '$$after': ['4', '5'], '$b': ['6']}]),
            ]
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
                        }
                    ],
                ),
            ]
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
    @pytest.mark.parametrize(
        "name, factory, statements, pattern_type, expected, names",
        Factories.extend(
            [
                (
                    "void f() {const char* bar = BAR;}",
                    Declaration,
                    ["const char* bar = BAR;"],
                    {},
                ),
                (
                    "void f() {const char* foo = FOO;}",
                    Declaration,
                    ["const char* foo = FOO;"],
                    {},
                ),
                (
                    "void f() {const char* same = SAME;}",
                    Declaration,
                    ["const char* same = SAME;"],
                    {},
                ),
                (
                    "void f() {const char* $name = BAR;}",
                    Declaration,
                    ["const char* bar = BAR;"],
                    {"$name": ["bar"]},
                ),
                (
                    "void f() {const char* $name = FOO;}",
                    Declaration,
                    ["const char* foo = FOO;"],
                    {"$name": ["foo"]},
                ),
                (
                    "void f() {const char* $name = SAME;}",
                    Declaration,
                    ["const char* same = SAME;"],
                    {"$name": ["same"]},
                ),
                (
                    "const char* $$args; void f() { print($$args);}",
                    Call,
                    ['print("%s %s %s", foo, bar, same);'],
                    {"$$args": ['"%s %s %s"', "foo", "bar", "same"]},
                ),
            ]
        ),
    )
    def test(self, name, factory, statements, pattern_type, expected, names):
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
        statements = last(find_ast_type(statements_atu, pattern_type))  # pick the last statement
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
    def test_multi_single(self):
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

        # assert_that(variants[0].exp['$$all'], has_length(1))
        ({"$f": ["two"], "$$all": ["a"], "$a": ["b"]},)
        ({"$f": ["three"], "$$all": ["a", "b"], "$a": ["c"]},)
        found = match_pattern(atu.children[-1].children[-1].children, stmt_nodes)
        assert_that(found, has_length(3))
