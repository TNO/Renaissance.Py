import pytest
from hamcrest import assert_that, has_length, has_string, is_

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory


class TestClangAstNode:
    def test_is_same_node(self):
        factory = ASTFactory(ClangASTNode, [])
        src = CPatternFactory(factory).create_statements("a == 3;a == 3;")
        CPatternFactory(factory).create_statement("a == 3;")
        assert_that(src[0], is_(src[1]))

    def test_find_all_in_clang_list_with_expansion(self):
        factory = ASTFactory(ClangASTNode, [])
        src = CPatternFactory(factory).create_statement("a == 3;")
        assert_that("a", is_(src.children[0].children[0].properties["name"]))

    def test_marco_also_include_define(self):
        src = ClangASTNode.load_from_text('#define x "xxx"', "test.c")
        assert_that(src.children, has_length(1))

    def test_marco_also_include_define_signature(self):
        src = ClangASTNode.load_from_text('#define x "xxx"', "test.c")
        assert_that('#define x "xxx"', is_(src.children[-1].signature))

    def test_var_decl_includesemi_column(self):
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.children[-1].signature, is_("int x= 0;"))

    def test_var_decl_in_ancestor(self):
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.children[-1].children[-1].get_ancestor("VAR_DECL"))

    def test_var_decl_in_ancestor_of(self):
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.is_ancestor_of(src.children[-1].children[-1]))

    @pytest.mark.skip("last semicolon is cut off from decl")
    def test_var_decl_include_semi_column_and_keep_space(self):
        src = ClangASTNode.load_from_text("   int    x   =    0   ;", "test.c")
        assert_that(src.children[-1].signature, is_("   int    x   =    0   ;"))

    def test_struct_include_semicolon(self):
        src = ClangASTNode.load_from_text("struct s;", "test.c")
        assert_that(src.children[-1].signature, is_("struct s;"))

    @pytest.mark.skip("last semicolon is cut off from struct")
    def test_struct_include_semicolon_and_space(self):
        src = ClangASTNode.load_from_text("struct s{int x; int y;} ;", "test.c")
        assert_that("struct s{int x; int y;} ;", is_(src.children[-1].signature))

    def test_mix_of_macro_and_decl(self):
        src = ClangASTNode.load_from_text(
            """
        #define FOO "foo"
        #define BAR "bar"
        #define SAME "bar"
        struct A_Struct{
            int a;
            int b;
        };
        typedef struct A_Struct A;
        int some_decl = 1;

        int print(const char*, const char *, const char *, const char*);
        void f(){
            A a = {};
            const char* foo = FOO;
            const char* bar = BAR;
            const char* same = SAME;
            print("%s %s %s", foo, bar, same);

        }""",
            "test.c",
        )
        assert_that(src.children, has_length(8))
        assert_that(src.children[0], has_string('(MacroDef, FOO, test.c[9:26]): |#define FOO "foo"|\n'))
        assert_that(src.children[1], has_string('(MacroDef, BAR, test.c[35:52]): |#define BAR "bar"|\n'))
        assert_that(src.children[2], has_string('(MacroDef, SAME, test.c[61:79]): |#define SAME "bar"|\n'))
        assert_that(
            src.children[3],
            has_string(
                "(StructDef, struct A_Struct, test.c[88:153]):\n    |struct A_Struct{|\n    |            int a;|\n"
                "    |            int b;|\n    |        };|\n"
            ),
        )
        assert_that(src.children[4], has_string("(TypedefDef, A, test.c[162:187]): |typedef struct A_Struct A|\n"))
        assert_that(src.children[5], has_string("(VariableDef, some_decl, test.c[197:215]): |int some_decl = 1;|\n"))
        assert_that(
            src.children[6],
            has_string("(FunctionDef, print, test.c[226:289]): |int print(const char*, const char *, const char *, const char*)|\n"),
        )
        assert_that(
            src.children[7],
            has_string(
                "(FunctionDef, f, test.c[299:495]):\n"
                "    |void f(){|\n"
                "    |            A a = {};|\n"
                "    |            const char* foo = FOO;|\n"
                "    |            const char* bar = BAR;|\n"
                "    |            const char* same = SAME;|\n"
                '    |            print("%s %s %s", foo, bar, same);|\n'
                "    ||\n"
                "    |        }|\n"
            ),
        )
