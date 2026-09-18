import pytest
from hamcrest import assert_that, contains_string, greater_than_or_equal_to, is_, less_than_or_equal_to, not_, not_none

from c_cpp.factories import Factories
from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.clang.c_pattern_factory import derive_header_text
from renaissance.integrations.clang.predicates import is_clang_compound_statement, is_clang_declaration_reference
from renaissance.syntax_tree import ASTShower
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.semantic_kind import SemanticKind


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
            if c.is_part_of_translation_unit()
            and not (c.semantic_kind is SemanticKind.FUNCTION and is_clang_compound_statement(c.children[-1]))
        )

        assert_that(header, contains_string('#define FOO "foo";'))
        assert_that(header, contains_string("int print(const char*,...);"))
        assert_that(header, contains_string("typedef struct A_Struct"))
        assert_that(header, contains_string("int some_decl = 1;"))
        assert_that(header, not_(contains_string("A a = {};")))
        assert_that(simple_header, contains_string('#define FOO "foo"'))
        assert_that(simple_header, contains_string("int print(const char*,...);"))
        assert_that(simple_header, contains_string("typedef struct A_Struct"))
        assert_that(simple_header, contains_string("int some_decl = 1;"))
        # assert_that(simple_header, not_(contains_string('A a = {};')))

        assert_that(header, not_(contains_string("#include <stdint.h>")))
        assert_that(simple_header, contains_string("#include <stdint.h>"))


class TestExpression:
    @pytest.mark.parametrize(
        "_, factory, expression, expected",
        Factories.extend(
            [
                (
                    "a == $hallo",
                    (
                        "(binary_operation, ==, test.c[123:134]): |a == $hallo|\n  (UNEXPOSED_EXPR, a, test.c[123:124]): |a|\n"
                        "    (DECL_REF_EXPR, a, test.c[123:124]): |a|\n  (MatchOne, $hallo, test.c[128:134]): |$hallo|\n"
                        "    (MatchOne, $hallo, test.c[128:134]): |$hallo|\n"
                    ),
                ),
                (
                    "2 != 3",
                    (
                        "(binary_operation, !=, test.c[105:111]): |2 != 3|\n  (literal, , test.c[105:106]): |2|\n"
                        "  (literal, , test.c[110:111]): |3|\n"
                    ),
                ),
                (
                    "a != b",
                    (
                        "(binary_operation, !=, test.c[118:124]): |a != b|\n  (UNEXPOSED_EXPR, a, test.c[118:119]): |a|\n"
                        "    (DECL_REF_EXPR, a, test.c[118:119]): |a|\n  (UNEXPOSED_EXPR, b, test.c[123:124]): |b|\n"
                        "    (DECL_REF_EXPR, b, test.c[123:124]): |b|\n"
                    ),
                ),
                (
                    "b != $world",
                    (
                        "(binary_operation, !=, test.c[123:134]): |b != $world|\n  (UNEXPOSED_EXPR, b, test.c[123:124]): |b|\n"
                        "    (DECL_REF_EXPR, b, test.c[123:124]): |b|\n  (MatchOne, $world, test.c[128:134]): |$world|\n"
                        "    (MatchOne, $world, test.c[128:134]): |$world|\n"
                    ),
                ),
                (
                    "c > $foo",
                    (
                        "(binary_operation, >, test.c[121:129]): |c > $foo|\n  (UNEXPOSED_EXPR, c, test.c[121:122]): |c|\n"
                        "    (DECL_REF_EXPR, c, test.c[121:122]): |c|\n  (MatchOne, $foo, test.c[125:129]): |$foo|\n"
                        "    (MatchOne, $foo, test.c[125:129]): |$foo|\n"
                    ),
                ),
                (
                    "d < $bar",
                    (
                        "(binary_operation, <, test.c[121:129]): |d < $bar|\n  (UNEXPOSED_EXPR, d, test.c[121:122]): |d|\n"
                        "    (DECL_REF_EXPR, d, test.c[121:122]): |d|\n  (MatchOne, $bar, test.c[125:129]): |$bar|\n"
                        "    (MatchOne, $bar, test.c[125:129]): |$bar|\n"
                    ),
                ),
                (
                    "e >= $baz",
                    (
                        "(binary_operation, >=, test.c[121:130]): |e >= $baz|\n  (UNEXPOSED_EXPR, e, test.c[121:122]): |e|\n"
                        "    (DECL_REF_EXPR, e, test.c[121:122]): |e|\n  (MatchOne, $baz, test.c[126:130]): |$baz|\n"
                        "    (MatchOne, $baz, test.c[126:130]): |$baz|\n"
                    ),
                ),
                (
                    "f <= $qux",
                    (
                        "(binary_operation, <=, test.c[121:130]): |f <= $qux|\n  (UNEXPOSED_EXPR, f, test.c[121:122]): |f|\n"
                        "    (DECL_REF_EXPR, f, test.c[121:122]): |f|\n  (MatchOne, $qux, test.c[126:130]): |$qux|\n"
                        "    (MatchOne, $qux, test.c[126:130]): |$qux|\n"
                    ),
                ),
                (
                    "g--",
                    "(unary_operation, , test.c[111:114]): |g--|\n  (DECL_REF_EXPR, g, test.c[111:112]): |g|\n",
                ),
                (
                    "h++",
                    "(unary_operation, , test.c[111:114]): |h++|\n  (DECL_REF_EXPR, h, test.c[111:112]): |h|\n",
                ),
                (
                    "!i",
                    (
                        "(unary_operation, , test.c[111:113]): |!i|\n  (UNEXPOSED_EXPR, i, test.c[112:113]): |i|\n"
                        "    (DECL_REF_EXPR, i, test.c[112:113]): |i|\n"
                    ),
                ),
            ],
        ),
    )
    def test(self, _, factory, expression, expected):
        pattern_factory = CPatternFactory(factory)
        node = pattern_factory.create_expression(expression)
        text = ASTShower.get_node(node)
        if isinstance(node, ClangASTNode):
            assert_that(text, is_(expected))
        else:
            assert_that(text, not_none())


class TestDeclaration:
    @pytest.mark.parametrize(
        "_, factory, declaration_text, types, parameters, expected_vars, expected_refs",
        Factories.extend(
            [
                ("int a=3;", [], [], 1, 0),
                ("int a;", [], [], 1, 0),
                ("int a = $x;", [], ["$x"], 1, 1),
                ("int a=2,b = 3;int c=4;", [], [], 3, 0),
                ("$type a = $x;", ["$type"], ["$x"], 1, 1),
                ("$type a,b = $x;", ["$type"], ["$x"], 2, 1),
            ],
        ),
    )
    def test(
        self,
        _,
        factory,
        declaration_text,
        types,
        parameters,
        expected_vars,
        expected_refs,
    ):
        pattern_factory = CPatternFactory(factory)
        created_declarations = list(pattern_factory.create_declarations(declaration_text, parameters=parameters, types=types))

        count_refs = 0
        count_vars = 0
        for decl in created_declarations:
            count_refs += len(find_nodes(decl, lambda node: is_clang_declaration_reference(node) or node.pattern_kind is not None))
            count_vars += len(find_nodes(decl, lambda node: node.semantic_kind is SemanticKind.DECLARATION))
            ASTShower.show_node(decl)
        assert_that(count_vars, is_(expected_vars))
        assert_that(count_refs, greater_than_or_equal_to(expected_refs))


class TestStatements:
    @pytest.mark.parametrize(
        "_, factory, statement_text, extra_declarations, expected_stmts, expected_refs",
        list(
            Factories.extend(
                [
                    ("a=3;", [], 1, 1),
                    ("a = b;", [], 1, 2),
                    ("a = $x;", [], 1, 2),
                    ("a=2;b = 3;c=4;", [], 3, 3),
                    ("a = ($type)$x;", ["typedef int $type;"], 1, 2),
                    ("a = f($x);", ["int f(int);"], 1, 3),
                ],
            ),
        ),
    )
    def test(
        self,
        _,
        factory,
        statement_text,
        extra_declarations,
        expected_stmts,
        expected_refs,
    ):
        pattern_factory = CPatternFactory(factory)
        created_statements = list(pattern_factory.create_statements(statement_text, extra_declarations=extra_declarations))

        count_refs = 0
        for decl in created_statements:
            count_refs += len(find_nodes(decl, lambda node: is_clang_declaration_reference(node) or node.pattern_kind is not None))
        assert_that(expected_stmts, is_(len(created_statements)))
        assert_that(expected_refs, less_than_or_equal_to(count_refs))
        for stmt in created_statements:
            assert_that(stmt.is_statement)


class TestUseAtuToCreatePatterns:
    """Test the creation of a complex pattern that includes a typedef, a struct, a define and a statement.

    Complex pattern take the includes, defines and typedefs from the translation unit

    """

    @pytest.mark.parametrize(
        "_, factory, statement_text, expected_stmts, expected_refs",
        list(
            Factories.extend(
                [
                    ("A a = {};", 1, 1),
                    ("const char* foo=FOO;", 1, 2),
                    ("const char* $x = BAR;", 1, 2),
                ],
            ),
        ),
    )
    def test(self, _, factory, statement_text, expected_stmts, expected_refs):
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
        pattern_factory = CPatternFactory(factory, atu)

        # pick the last statement for match
        pattern_root = pattern_factory.create(statement_text)

        # the user must pick it's own pattern in this case the last statement
        assert_that(pattern_root.children[-1].is_statement)
        if _ == "clang_json":
            pytest.xfail("Clang JSON source offsets currently truncate reconstructed header text")
        assert statement_text.replace(" ", "") in pattern_root.signature.replace(" ", "")

        statement = pattern_factory.create_statement(
            "a == 3;",
            kind=lambda node: node.semantic_kind is SemanticKind.BINARY_OPERATION,
        )

        assert statement.semantic_kind is SemanticKind.BINARY_OPERATION
