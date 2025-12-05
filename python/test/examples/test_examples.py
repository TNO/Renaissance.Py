from typing import Callable
from unittest import TestCase

from parameterized import parameterized
from syntax_tree.ast_node import ASTNode


from examples.refactor_with_nested_compositions import refactor_with_nested_compositions, expected_result as expected_result_nested
from examples.replace_if_with_ternary import replace_if_with_ternary, expected_result as expected_result_ternary
from examples.remove_unused_variable import remove_unused_variable_using_refactor_method, remove_unused_variable_low_level
from examples.refactor_examples_different_styles import example_add_comment_and_commit, example_use_ast_kind_finder, example_use_ast_function_finder, example_replace_old_by_fancy_new
from test.c_cpp.factories import Factories
from syntax_tree import CPatternFactory, ASTFactory

class TestRefactorWithNestedCompositions(TestCase):

    def test_refactor_with_nested_compositions(self):
        result =  refactor_with_nested_compositions(['', ''])
        assert result
        self.assertMultiLineEqual(result, expected_result_nested)


class TestReplaceIfWithTernaryOperator(TestCase):

    def test_refactor_with_nested_compositions(self):
        result =  replace_if_with_ternary()
        assert result
        self.assertMultiLineEqual(result, expected_result_ternary)

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
        ('cmt',example_add_comment_and_commit),
        ('kind',example_use_ast_kind_finder),
        ('function',example_use_ast_function_finder),
        ('match',example_replace_old_by_fancy_new),

    ])))
    def test(self, _, factory: ASTFactory, _node_type : type[ASTNode], method: Callable[[ASTFactory, CPatternFactory], tuple[str, str]]):
        pattern_factory = CPatternFactory(factory)
        result, expected = method(factory, pattern_factory)
        assert result
        self.assertMultiLineEqual(result, expected)

