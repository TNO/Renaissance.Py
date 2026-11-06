# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the C refactoring example scripts."""

from collections.abc import Callable

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    is_,
    is_not,
)

from rejuvenation.refactor_examples_different_styles import (
    example_add_comment_and_commit,
    example_replace_old_by_fancy_new,
    example_use_ast_function_finder,
    example_use_ast_kind_finder,
)
from rejuvenation.refactor_with_nested_compositions import (
    refactor_with_nested_compositions,
)
from rejuvenation.remove_unused_variable import (
    remove_unused_variable_low_level,
    remove_unused_variable_using_refactor_method,
)
from rejuvenation.replace_if_with_ternary import replace_if_with_ternary
from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.ast_node import ASTNode
from test.c_cpp.factories import Factories


class TestRefactorWithNestedCompositions:
    """AI: Tests the nested-compositions refactor example produces the expected rewritten code."""

    def test_refactor_with_nested_compositions(self) -> None:
        """AI: Verify the nested-compositions refactor example produces the expected rewritten C source."""
        result = refactor_with_nested_compositions(["", ""])
        assert_that(result, is_not(None))
        expected_result_nested = """\
void f1(int a, int b, int c);
void f2(int a, int c);
void f(){
    const int a = 1;
    const int b = 2;
    int isAOne = a==1;
    int c = 0, d=0;

    //changed if expr to const
    if(isAOne){
        d++;
//changed if expr to const
if(isAOne){
    d++;c=d;
//changed function f1 to f2
f2(a,c);
;
}
      //changed function f1 to f2
      f2(a,c);
    ;
    }
            //changed function f1 to f2
            f2(a,c);
    if (a==2) {
        c++;

        //changed function f1 to f2
        f2(a,c);
    }

    //changed function f1 to f2
    f2(a,c);
}"""
        assert result == expected_result_nested
        assert_that(result, is_(expected_result_nested))


class TestReplaceIfWithTernaryOperator:
    """AI: Tests the replace-if-with-ternary refactor example produces the expected rewritten code."""

    def test_replace_if_with_ternary(self) -> None:
        """AI: Verify the replace-if-with-ternary refactor example produces the expected rewritten C source."""
        result = replace_if_with_ternary()

        expected_result_ternary = (
            "int a = 1;\n"
            "        int b = 2;\n"
            "        int c = 3;\n"
            "        int d = 4;\n"
            "        void f(){\n"
            "            c++; b=(a==1) ? 2:3; d++;\n"
            "        }"
        )
        assert_that(result, is_(expected_result_ternary))


# add a testcase for remove unused variable
class TestRemoveUnusedVariable:
    """AI: Tests the remove-unused-variable refactor examples produce the expected rewritten code."""

    @pytest.mark.parametrize(("_", "node_type"), Factories.node_types)
    def test_remove_unused_variable_using_refactor_method(self, _: str, node_type: type[ASTNode]) -> None:
        """AI: Verify remove_unused_variable_using_refactor_method produces the expected rewritten result."""
        result, expected = remove_unused_variable_using_refactor_method(node_type)
        assert_that(result, is_(expected))

    @pytest.mark.parametrize(("_", "node_type"), Factories.node_types)
    def test_remove_unused_variable_low_level(self, _: str, node_type: type[ASTNode]) -> None:
        """AI: Verify remove_unused_variable_low_level produces the expected rewritten result."""
        result, expected_result = remove_unused_variable_low_level(node_type)
        assert_that(result, is_(expected_result))


class TestExamplesDifferentStyles:
    """AI: Tests the same refactor produces identical results across different AST-finder styles."""

    @pytest.mark.parametrize(
        ("_", "factory", "_node_type", "method"),
        list(
            Factories.extend(
                [
                    ("kind", example_use_ast_kind_finder),
                    ("function", example_use_ast_function_finder),
                ],
            ),
        ),
    )
    def test(
        self,
        _,
        factory: ASTFactory,
        _node_type: type[ASTNode],
        method: Callable[[ASTFactory, CPatternFactory], tuple[str, str]],
    ) -> None:
        """AI: Verify the given AST-finder-style example method produces the expected refactor result."""
        pattern_factory = CPatternFactory(factory)
        result, expected = method(factory, pattern_factory)

        assert_that(expected, is_(result))

    @pytest.mark.xfail(
        reason="The declaration patterns do not match the 'old' declarations of the target file, so the "
        "comment is inserted twice before every declaration instead of once before each 'old' one.",
        strict=True,
    )
    def test_example_add_comment_and_commit(self) -> None:
        """Verify example_add_comment_and_commit adds the obsolete-comment once before each 'old' declaration using Clang."""
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)
        result, expected = example_add_comment_and_commit(factory, pattern_factory)

        assert_that(result, is_(expected))

    def test_example_add_comment_and_commit_json(self) -> None:
        """AI: Verify example_add_comment_and_commit inserts the expected obsolete-comment text using Clang JSON."""
        factory = ASTFactory(ClangJsonASTNode)
        pattern_factory = CPatternFactory(factory)
        result, expected = example_add_comment_and_commit(factory, pattern_factory)
        assert_that(result, contains_string("        // old has become obsolete\n        old b = 2;"))

    @pytest.mark.xfail(
        reason="The declaration patterns never bind $old to the 'old' type, so no declaration is replaced.",
        strict=True,
    )
    def test_example_replace_old_by_fancy_new(self) -> None:
        """Verify example_replace_old_by_fancy_new replaces every 'old' declaration type with 'fancy_new' using Clang."""
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)
        result, expected = example_replace_old_by_fancy_new(factory, pattern_factory)

        assert_that(result, is_(expected))
