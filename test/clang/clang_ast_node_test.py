import unittest

from hamcrest import assert_that, is_

from renaissance.impl.clang import ClangASTNode
from renaissance.syntax_tree import CPatternFactory, ASTFactory


def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    assert src.children[0].children[0].properties['name'] == 'a'


def test_marco_also_include_define():
    src = ClangASTNode.load_from_text('#define x "xxx"', 'test.c', [], None)
    assert len(src.children) == 1


def test_marco_also_include_define():
    src = ClangASTNode.load_from_text('#define x "xxx"', 'test.c', [], None)
    assert src.children[-1].signature == '#define x "xxx"'


def test_var_decl_includesemi_column():
    src = ClangASTNode.load_from_text('int x= 0;', 'test.c', [], None)
    assert_that(src.children[-1].signature, is_('int x= 0;'))


@unittest.skip("last semicolumn is cut off from decl")
def test_var_decl_include_semi_column_and_keep_space():
    src = ClangASTNode.load_from_text('   int    x   =    0   ;', 'test.c', [], None)
    assert_that(src.children[-1].signature, is_('   int    x   =    0   ;'))


def test_struct_include_semicolumn():
    src = ClangASTNode.load_from_text('struct s;', 'test.c', [], None)
    assert_that(src.children[-1].signature, is_('struct s;'))


@unittest.skip("last semicolumn is cut off from struct")
def test_struct_include_semicolumn_and_space():
    src = ClangASTNode.load_from_text('struct s{int x; int y;} ;', 'test.c', [], None)
    assert src.children[-1].signature == 'struct s{int x; int y;} ;'


def test_mix_of_macro_and_decl():
    src = ClangASTNode.load_from_text('''
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

        }''', 'test.c', [], None)
    assert len(src.children) == 8
    assert str(src.children[0]) == '(MACRO_DEFINITION, FOO, test.c[9:26]): |#define FOO "foo"|\n'
    assert str(src.children[1]) == '(MACRO_DEFINITION, BAR, test.c[35:52]): |#define BAR "bar"|\n'
    assert str(src.children[2]) == '(MACRO_DEFINITION, SAME, test.c[61:79]): |#define SAME "bar"|\n'
    assert str(src.children[3]) == (
        '(STRUCT_DECL, struct A_Struct, test.c[88:153]):\n    |struct A_Struct{|\n    |            int a;|\n    |            int b;|\n    |        };|\n')
    assert str(src.children[4]) == '(TYPEDEF_DECL, A, test.c[162:187]): |typedef struct A_Struct A|\n'
    assert str(src.children[5]) == '(VAR_DECL, some_decl, test.c[197:215]): |int some_decl = 1;|\n'
    assert str(src.children[6]) == ('(FUNCTION_DECL, print, test.c[226:289]): |int print(const char*, const char '
                                    '*, const char *, const char*)|\n')
    assert str(src.children[7]) == ('(FUNCTION_DECL, f, test.c[299:495]):\n'
                                    '    |void f(){|\n'
                                    '    |            A a = {};|\n'
                                    '    |            const char* foo = FOO;|\n'
                                    '    |            const char* bar = BAR;|\n'
                                    '    |            const char* same = SAME;|\n'
                                    '    |            print("%s %s %s", foo, bar, same);|\n'
                                    '    ||\n'
                                    '    |        }|\n')
