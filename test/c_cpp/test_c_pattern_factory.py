import pytest
from hamcrest import *
from hamcrest import assert_that, contains_string
from mako.testing.assertions import not_in
from more_itertools import last

from c_cpp.factories import Factories
from renaissance.impl.clang import CPatternFactory, ClangASTNode
from renaissance.impl.clang.c_pattern_factory import derive_header_text
from renaissance.impl.types import DeclarationExpression, MatchOne, VariableDeclaration
from renaissance.syntax_tree import ASTFinder, ASTShower
from renaissance.syntax_tree.ast_finder import find_ast_type


class TestCPatternFactory:
    def test_derive_header(self):
        code = """
                #include <stdint.h>
                int print(const char*,...);
                #define FOO "foo"
                #define BAR "bar"
                #define SAME "bar"
                typedef struct A_Struct{
                    int a;
                    int b;
                } A;
                int some_decl = 1; 

                void f(){
                    A a = {};
                    const char* foo = FOO;
                    const char* bar = BAR;
                    const char* same = SAME;
                    print("%s %s %s", foo, bar, same);

                }

        """
        atu = ClangASTNode.load_from_text(code, "test.c", [], None)
        ASTShower.show_node(atu)

        header, lang = derive_header_text("c", atu)
        simple_header = ";\n".join(
            c.signature
            for c in atu.children
            if c.is_part_of_translation_unit() and not (c.kind == "FUNCTION_DECL" and c.children[-1].kind == "COMPOUND_STMT")
        )

        assert_that(header, contains_string('#include <stdint.h>'))
        assert_that(header, contains_string('#define FOO "foo";'))
        assert_that(header, contains_string("int print(const char*,...);"))
        assert_that(header, contains_string("typedef struct A_Struct"))
        assert_that(header, contains_string("int some_decl = 1;"))
        assert_that(header, not_(contains_string('A a = {};')))
        assert_that(simple_header, contains_string('#include <stdint.h>'))
        assert_that(simple_header, contains_string('#define FOO "foo"'))
        assert_that(simple_header, contains_string("int print(const char*,...);"))
        assert_that(simple_header, contains_string("typedef struct A_Struct"))
        assert_that(simple_header, contains_string("int some_decl = 1;"))
        assert_that(simple_header, not_(contains_string('A a = {};')))


class TestExpression(TestCPatternFactory):

    @pytest.mark.parametrize(
        "_, factory, expression, expected",
        Factories.extend(
            [
                (
                    "a == $hallo",
                    "(BINARY_OPERATOR, , test.c[123:134]): |a == $hallo|\n  (UNEXPOSED_EXPR, a, test.c[123:124]): |a|\n    (DECL_REF_EXPR, a, test.c[123:124]): |a|\n  (MatchOne, $hallo, test.c[128:134]): |$hallo|\n    (MatchOne, $hallo, test.c[128:134]): |$hallo|\n",
                ),
                (
                    "2 != 3",
                    "(BINARY_OPERATOR, , test.c[105:111]): |2 != 3|\n  (INTEGER_LITERAL, , test.c[105:106]): |2|\n  (INTEGER_LITERAL, , test.c[110:111]): |3|\n",
                ),
                (
                    "a != b",
                    "(BINARY_OPERATOR, , test.c[118:124]): |a != b|\n  (UNEXPOSED_EXPR, a, test.c[118:119]): |a|\n    (DECL_REF_EXPR, a, test.c[118:119]): |a|\n  (UNEXPOSED_EXPR, b, test.c[123:124]): |b|\n    (DECL_REF_EXPR, b, test.c[123:124]): |b|\n",
                ),
                (
                    "b != $world",
                    "(BINARY_OPERATOR, , test.c[123:134]): |b != $world|\n  (UNEXPOSED_EXPR, b, test.c[123:124]): |b|\n    (DECL_REF_EXPR, b, test.c[123:124]): |b|\n  (MatchOne, $world, test.c[128:134]): |$world|\n    (MatchOne, $world, test.c[128:134]): |$world|\n",
                ),
                (
                    "c > $foo",
                    "(BINARY_OPERATOR, , test.c[121:129]): |c > $foo|\n  (UNEXPOSED_EXPR, c, test.c[121:122]): |c|\n    (DECL_REF_EXPR, c, test.c[121:122]): |c|\n  (MatchOne, $foo, test.c[125:129]): |$foo|\n    (MatchOne, $foo, test.c[125:129]): |$foo|\n",
                ),
                (
                    "d < $bar",
                    "(BINARY_OPERATOR, , test.c[121:129]): |d < $bar|\n  (UNEXPOSED_EXPR, d, test.c[121:122]): |d|\n    (DECL_REF_EXPR, d, test.c[121:122]): |d|\n  (MatchOne, $bar, test.c[125:129]): |$bar|\n    (MatchOne, $bar, test.c[125:129]): |$bar|\n",
                ),
                (
                    "e >= $baz",
                    "(BINARY_OPERATOR, , test.c[121:130]): |e >= $baz|\n  (UNEXPOSED_EXPR, e, test.c[121:122]): |e|\n    (DECL_REF_EXPR, e, test.c[121:122]): |e|\n  (MatchOne, $baz, test.c[126:130]): |$baz|\n    (MatchOne, $baz, test.c[126:130]): |$baz|\n",
                ),
                (
                    "f <= $qux",
                    "(BINARY_OPERATOR, , test.c[121:130]): |f <= $qux|\n  (UNEXPOSED_EXPR, f, test.c[121:122]): |f|\n    (DECL_REF_EXPR, f, test.c[121:122]): |f|\n  (MatchOne, $qux, test.c[126:130]): |$qux|\n    (MatchOne, $qux, test.c[126:130]): |$qux|\n",
                ),
                (
                    "g--",
                    "(UNARY_OPERATOR, , test.c[111:114]): |g--|\n  (DECL_REF_EXPR, g, test.c[111:112]): |g|\n",
                ),
                (
                    "h++",
                    "(UNARY_OPERATOR, , test.c[111:114]): |h++|\n  (DECL_REF_EXPR, h, test.c[111:112]): |h|\n",
                ),
                (
                    "!i",
                    "(UNARY_OPERATOR, , test.c[111:113]): |!i|\n  (UNEXPOSED_EXPR, i, test.c[112:113]): |i|\n    (DECL_REF_EXPR, i, test.c[112:113]): |i|\n",
                ),
            ]
        ),
    )
    def test(self, _, factory, expression, expected):
        patternFactory = CPatternFactory(factory)
        node = patternFactory.create_expression(expression)
        text = ASTShower.get_node(node)
        if isinstance(node, ClangASTNode):
            assert_that(text, is_(expected))
        else:
            assert_that(text, not_none())


class TestDeclaration(TestCPatternFactory):

    @pytest.mark.parametrize(
        "_, factory, declarationText, types, parameters, expected_vars, expected_refs",
        Factories.extend(
            [
                ("int a=3;", [], [], 1, 0),
                ("int a;", [], [], 1, 0),
                ("int a = $x;", [], ["$x"], 1, 1),
                ("int a=2,b = 3;int c=4;", [], [], 3, 0),
                ("$type a = $x;", ["$type"], ["$x"], 1, 1),
                ("$type a,b = $x;", ["$type"], ["$x"], 2, 1),
            ]
        ),
    )
    def test(
        self,
        _,
        factory,
        declarationText,
        types,
        parameters,
        expected_vars,
        expected_refs,
    ):
        patternFactory = CPatternFactory(factory)
        created_declarations = list(patternFactory.create_declarations(declarationText, parameters=parameters, types=types))

        count_refs = 0
        count_vars = 0
        for decl in created_declarations:
            count_refs += len(find_ast_type(decl, (DeclarationExpression,MatchOne)))
            count_vars += len(find_ast_type(decl, VariableDeclaration))
            ASTShower.show_node(decl)
        assert_that(count_vars, is_(expected_vars))
        assert_that(count_refs, greater_than_or_equal_to(expected_refs))


class TestStatements(TestCPatternFactory):

    @pytest.mark.parametrize(
        "_, factory, statementText, extra_declarations, expected_stmts, expected_refs",
        list(
            Factories.extend(
                [
                    ("a=3;", [], 1, 1),
                    ("a = b;", [], 1, 2),
                    ("a = $x;", [], 1, 2),
                    ("a=2;b = 3;c=4;", [], 3, 3),
                    ("a = ($type)$x;", ["typedef int $type;"], 1, 2),
                    ("a = f($x);", ["int f(int);"], 1, 3),
                ]
            )
        ),
    )
    def test(
        self,
        _,
        factory,
        statementText,
        extra_declarations,
        expected_stmts,
        expected_refs,
    ):
        patternFactory = CPatternFactory(factory)
        created_statements = list(patternFactory.create_statements(statementText, extra_declarations=extra_declarations))

        count_refs = 0
        for decl in created_statements:
            count_refs += len(find_ast_type(decl, (DeclarationExpression,MatchOne)))
        assert_that(expected_stmts, is_(len(created_statements)))
        assert_that(expected_refs, less_than_or_equal_to(count_refs))
        for stmt in created_statements:
            assert_that(stmt.is_statement)


class TestUseAtuToCreatePatterns(TestCPatternFactory):
    """
    Test the creation of a complex pattern that includes a typedef, a struct, a define and a statement

    Complex pattern take the includes, defines and typedefs from the translation unit

    """

    @pytest.mark.parametrize(
        "_, factory, statementText, expected_stmts, expected_refs",
        list(
            Factories.extend(
                [
                    ("A a = {};", 1, 1),
                    ("const char* foo=FOO;", 1, 2),
                    ("const char* $x = BAR;", 1, 2),
                ]
            )
        ),
    )
    def test(self, _, factory, statementText, expected_stmts, expected_refs):
        code = """
        int print(const char*,const char*,const char*,const char*);
        #define FOO "foo"
        #define BAR "bar"
        #define SAME "bar"
        typedef struct A_Struct{
            int a;
            int b;
        } A;
        int some_decl = 1; 

        void f(){
            A a = {};
            const char* foo = FOO;
            const char* bar = BAR;
            const char* same = SAME;
            print("%s %s %s", foo, bar, same);

        }

"""
        atu = factory.create_from_text(code, "example.c")

        # ASTShower.show_node(atu, include_properties=True)
        # use the factory and the translation unit (for include, define and typedef reference) to create a pattern factory
        patternFactory = CPatternFactory(factory, atu)

        # pick the last statement  fo match
        pattern_root = patternFactory.create(statementText)

        # the user must pick it's own pattern in this case the last statement
        assert_that(pattern_root.children[-1].is_statement)
        node = last(n for n in pattern_root.children if n.kind != "UNEXPOSED_DECL")
        raw = node.signature

        assert_that(statementText, starts_with(raw))
