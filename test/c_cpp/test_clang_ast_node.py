"""Tests for the Clang-backed ASTNode implementation."""

import pytest
from hamcrest import assert_that, has_length, has_string, is_

from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory


class TestClangAstNode:
    """AI: Tests for the Clang-backed ASTNode implementation."""

    def test_is_same_node(self):
        """AI: Verify two occurrences of an identical pattern statement resolve to the same node."""
        factory = ASTFactory(ClangASTNode, [])
        src = CPatternFactory(factory).create_statements("a == 3;a == 3;")
        CPatternFactory(factory).create_statement("a == 3;")
        assert_that(src[0], is_(src[1]))

    def test_find_all_in_clang_list_with_expansion(self):
        """AI: Verify a declaration reference node's name property is populated within a Clang AST list."""
        factory = ASTFactory(ClangASTNode, [])
        src = CPatternFactory(factory).create_statement("a == 3;")
        assert_that("a", is_(src.children[0].children[0].properties["name"]))

    def test_marco_also_include_define(self):
        """AI: Verify a #define macro is parsed as a single child node."""
        src = ClangASTNode.load_from_text('#define x "xxx"', "test.c")
        assert_that(src.children, has_length(1))

    def test_marco_also_include_define_signature(self):
        """AI: Verify a #define macro's signature text matches the original source."""
        src = ClangASTNode.load_from_text('#define x "xxx"', "test.c")
        assert_that('#define x "xxx"', is_(src.children[-1].signature))

    def test_var_decl_includesemi_column(self):
        """AI: Verify a variable declaration's signature includes its trailing semicolon."""
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.children[-1].signature, is_("int x= 0;"))

    def test_var_decl_in_ancestor(self):
        """AI: Verify get_ancestor finds the enclosing VAR_DECL ancestor node."""
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.children[-1].children[-1].get_ancestor("VAR_DECL"))

    def test_var_decl_in_ancestor_of(self):
        """AI: Verify is_ancestor_of confirms the translation unit is an ancestor of a nested declaration node."""
        src = ClangASTNode.load_from_text("int x= 0;", "test.c")
        assert_that(src.is_ancestor_of(src.children[-1].children[-1]))

    @pytest.mark.skip("last semicolon is cut off from decl")
    def test_var_decl_include_semi_column_and_keep_space(self):
        """AI: Verify a variable declaration's signature preserves surrounding whitespace and trailing semicolon."""
        src = ClangASTNode.load_from_text("   int    x   =    0   ;", "test.c")
        assert_that(src.children[-1].signature, is_("   int    x   =    0   ;"))

    @pytest.mark.skip(
        "https://github.com/TNO/Renaissance.Py/issues/154 - load_from_text() caches file "
        "content encoded with sys.getfilesystemencoding(), but libclang always parses/offsets "
        "unsaved_files content as UTF-8 internally. When the filesystem encoding is not UTF-8, "
        "a multi-byte UTF-8 character earlier in the file shifts every subsequent byte offset, "
        "so slicing the (differently-sized) cached byte array with clang's offsets returns "
        "corrupted text.",
    )
    def test_signature_after_multibyte_char_when_filesystem_encoding_is_not_utf8(self, mocker):
        """AI: Verify a node's signature offsets remain correct after a multi-byte character when the filesystem encoding isn't UTF-8."""
        # 'é' encodes as 1 byte in latin-1 but 2 bytes in UTF-8. libclang parses/reports
        # offsets against a UTF-8 encoding of the source regardless of the platform's
        # filesystem encoding, so the two byte arrays diverge in length from this point on.
        mocker.patch("sys.getfilesystemencoding", return_value="latin-1")
        code = "// café\nint x = 0;\n"
        src = ClangASTNode.load_from_text(code, "test.c")
        assert_that(src.children[-1].signature, is_("int x = 0;"))

    def test_struct_include_semicolon(self):
        """AI: Verify a struct forward-declaration's signature includes its trailing semicolon."""
        src = ClangASTNode.load_from_text("struct s;", "test.c")
        assert_that(src.children[-1].signature, is_("struct s;"))

    @pytest.mark.skip("last semicolon is cut off from struct")
    def test_struct_include_semicolon_and_space(self):
        """AI: Verify a struct definition's signature includes trailing whitespace and semicolon."""
        src = ClangASTNode.load_from_text("struct s{int x; int y;} ;", "test.c")
        assert_that("struct s{int x; int y;} ;", is_(src.children[-1].signature))

    def test_mix_of_macro_and_decl(self):
        """AI: Verify a mix of macro defines and declarations parse correctly together."""
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
        assert_that(src.children[0], has_string('(MACRO_DEFINITION, FOO, test.c[9:26]): |#define FOO "foo"|\n'))
        assert_that(src.children[1], has_string('(MACRO_DEFINITION, BAR, test.c[35:52]): |#define BAR "bar"|\n'))
        assert_that(src.children[2], has_string('(MACRO_DEFINITION, SAME, test.c[61:79]): |#define SAME "bar"|\n'))
        assert_that(
            src.children[3],
            has_string(
                "(class, struct A_Struct, test.c[88:153]):\n    |struct A_Struct{|\n    |            int a;|\n"
                "    |            int b;|\n    |        };|\n",
            ),
        )
        assert_that(src.children[4], has_string("(declaration, A, test.c[162:187]): |typedef struct A_Struct A|\n"))
        assert_that(src.children[5], has_string("(declaration, some_decl, test.c[197:215]): |int some_decl = 1;|\n"))
        assert_that(
            src.children[6],
            has_string("(function, print, test.c[225:288]): |int print(const char*, const char *, const char *, const char*)|\n"),
        )
        assert_that(
            src.children[7],
            has_string(
                "(function, f, test.c[298:494]):\n"
                "    |void f(){|\n"
                "    |            A a = {};|\n"
                "    |            const char* foo = FOO;|\n"
                "    |            const char* bar = BAR;|\n"
                "    |            const char* same = SAME;|\n"
                '    |            print("%s %s %s", foo, bar, same);|\n'
                "    ||\n"
                "    |        }|\n",
            ),
        )
