from typing import Callable
from unittest import TestCase

from parameterized import parameterized

from c_cpp.factories import Factories
from refactor_examples_different_styles import example_use_ast_kind_finder, \
    example_use_ast_function_finder, example_add_comment_and_commit, example_replace_old_by_fancy_new
from refactor_with_nested_compositions import refactor_with_nested_compositions
from remove_unused_variable import remove_unused_variable_using_refactor_method, remove_unused_variable_low_level
from replace_if_with_ternary import replace_if_with_ternary
from syntax_tree import CPatternFactory, ASTFactory
from syntax_tree.ast_node import ASTNode


class TestRefactorWithNestedCompositions(TestCase):

    def test_refactor_with_nested_compositions(self):
        result =  refactor_with_nested_compositions(['', ''])
        assert result
        expected_result_nested=('void f1(int a, int b, int c);\n'
 'void f2(int a, int c);\n'
 'void f(){\n'
 '    const int a = 1;\n'
 '    const int b = 2;\n'
 '    int isAOne = a==1;\n'
 '    int c = 0, d=0;\n'
 '    //changed if expr to const\n'
 '    if(isAOne){\n'
 '       d++;//changed if expr to const\n'
 'if(isAOne){\n'
 '   d++;c=d;//changed function f1 to f2\n'
 'f2(a\n'
 ',c\n'
 ');\n'
 ';\n'
 '}\n'
 '    ;\n'
 '    }\n'
 '    if (a==2) {\n'
 '        c++;\n'
 '        //changed function f1 to f2\n'
 '        f2(a\n'
 '        ,c\n'
 '        );\n'
 '    }\n'
 '    //changed function f1 to f2\n'
 '    f2(a\n'
 '    ,c\n'
 '    );\n'
 '}')
        self.assertEqual(expected_result_nested,result)


class TestReplaceIfWithTernaryOperator(TestCase):

    # didn't check expected result
    def test_refactor_with_nested_compositions(self):
        result =  replace_if_with_ternary()
        assert result
        expected_result_ternary=('int a = 1;\n'
 '        int b = 2;\n'
 '        int c = 3;\n'
 '        int d = 4;\n'
 '        void f(){\n'
 '            if (a==1) {\n'
 '                c++;\n'
 '                b = 2;\n'
 '                d++;\n'
 '            }\n'
 '            else {\n'
 '                c++;\n'
 '                b = 3;\n'
 '                d++;\n'
 '            }\n'
 '        }')
        self.assertEqual( expected_result_ternary,result)

# add a testcase for remove unused variable
class TestRemoveUnusedVariable(TestCase):

    @parameterized.expand(Factories.node_types)
    def test_remove_unused_variable_using_refactor_method(self, _: str, node_type: type[ASTNode]):
        result, expected = remove_unused_variable_using_refactor_method(node_type)
        assert result
        self.assertMultiLineEqual(result, expected)

    @parameterized.expand(Factories.node_types)
    def test_remove_unused_variable_low_level(self, _: str, node_type: type[ASTNode]):
        result, expected_result = remove_unused_variable_low_level(node_type)
        assert result
        self.assertMultiLineEqual(result, expected_result)

class TestExamplesDifferentStyles(TestCase):

    @parameterized.expand(list(Factories.extend([
        ('kind',example_use_ast_kind_finder),
        ('function',example_use_ast_function_finder),
        # TODO: fix this 2 test
        # cmt macro got replace replaced to int in clang impl.
        # ('cmt',example_add_comment_and_commit),
        # $old $name is ambiguous (int) (a); or (int) (a=0);.
        # ('match',example_replace_old_by_fancy_new),

    ])))
    def test(self, _, factory: ASTFactory, _node_type : type[ASTNode], method: Callable[[ASTFactory, CPatternFactory], tuple[str, str]]):
        pattern_factory = CPatternFactory(factory)
        result, expected = method(factory, pattern_factory)
        assert result
        self.assertEqual(result, expected)

