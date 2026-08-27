from collections.abc import Callable

import pytest
from hamcrest import *

from c_cpp.factories import Factories
from rejuvenation.batch_process_examples import (
    batch_recipe_example,
    batch_remove_unused_variable_once_example,
    batch_repeat_example,
)
from rejuvenation.recipe_example import batch_recipe_example as receipe_example
from rejuvenation.refactor_examples_different_styles import (
    example_add_comment_and_commit,
    example_replace_old_by_fancy_new,
    example_use_ast_function_finder,
    example_use_ast_kind_finder,
    main,
)
from rejuvenation.refactor_with_nested_compositions import (
    refactor_with_nested_compositions,
)
from rejuvenation.remove_unused_variable import (
    remove_unused_variable_low_level,
    remove_unused_variable_using_refactor_method,
)
from rejuvenation.replace_if_with_ternary import replace_if_with_ternary
from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.ast_node import ASTNode


class TestRefactorWithNestedCompositions:
    def test_refactor_with_nested_compositions(self):
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
    # didn't check expected result
    def test_refactor_with_nested_compositions(self):
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
    @pytest.mark.parametrize("_, node_type", Factories.node_types)
    def test_remove_unused_variable_using_refactor_method(self, _: str, node_type: type[ASTNode]):
        result, expected = remove_unused_variable_using_refactor_method(node_type)
        assert_that(result, is_(expected))

    @pytest.mark.parametrize("_, node_type", Factories.node_types)
    def test_remove_unused_variable_low_level(self, _: str, node_type: type[ASTNode]):
        result, expected_result = remove_unused_variable_low_level(node_type)
        assert_that(result, is_(expected_result))


class TestExamplesDifferentStyles:
    @pytest.mark.parametrize(
        "_, factory, _node_type, method",
        list(
            Factories.extend(
                [
                    ("kind", example_use_ast_kind_finder),
                    ("function", example_use_ast_function_finder),
                ]
            )
        ),
    )
    def test(
        self,
        _,
        factory: ASTFactory,
        _node_type: type[ASTNode],
        method: Callable[[ASTFactory, CPatternFactory], tuple[str, str]],
    ):
        pattern_factory = CPatternFactory(factory)
        result, expected = method(factory, pattern_factory)

        assert_that(expected, is_(result))

    def test_example_add_comment_and_commit(self):
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)
        result, expected = example_add_comment_and_commit(factory, pattern_factory)

        assert_that(result, contains_string("// old has become obsolete\n        // old has become obsolete\n "))

    def test_example_add_comment_and_commit_json(self):
        factory = ASTFactory(ClangJsonASTNode)
        pattern_factory = CPatternFactory(factory)
        assert_that(calling(lambda: example_add_comment_and_commit(factory, pattern_factory)), not_(raises(Exception)))
        result, expected = example_add_comment_and_commit(factory, pattern_factory)
        assert_that(result, contains_string("        // old has become obsolete\n        old b = 2;"))

    def test_example_replace_old_by_fancy_new(self):
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)

        assert_that(calling(lambda: example_add_comment_and_commit(factory, pattern_factory)), not_(raises(Exception)))

        result, expected = example_replace_old_by_fancy_new(factory, pattern_factory)
        # shiould check this:
        # assert_that(result, contains_string("fancy_new b = 2;\n"))

    def test_make_sure_that_batch_proc_still_run(self):
        assert_that(calling(batch_remove_unused_variable_once_example), not_(raises(Exception)))

    def test_make_sure_that_batch_proc_still_run(self):
        assert_that(calling(batch_repeat_example), not_(raises(Exception)))

    def test_make_sure_that_batch_proc_still_run(self):
        assert_that(calling(batch_recipe_example), not_(raises(Exception)))

    def test_make_sure_that_recipe_still_run(self):
        assert_that(calling(receipe_example), raises(Exception, pattern="'stddef.h' file not found"))

    def test_make_sure_different_style_still_run(self):
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)

        assert_that(
            calling(lambda: example_add_comment_and_commit(factory, pattern_factory)),
            not_(raises(Exception)),
        )
        assert_that(
            calling(lambda: example_replace_old_by_fancy_new(factory, pattern_factory)),
            not_(raises(Exception)),
        )
        assert_that(
            calling(lambda: example_use_ast_kind_finder(factory, pattern_factory)),
            not_(raises(Exception)),
        )
        assert_that(
            calling(lambda: example_use_ast_function_finder(factory, pattern_factory)),
            not_(raises(Exception)),
        )
        assert_that(calling(lambda: main([])), not_(raises(Exception)))

    def test_make_sure_that_nested_compositions_still_run(self):
        assert_that(calling(lambda: refactor_with_nested_compositions([])), not_(raises(Exception)))

    @pytest.mark.parametrize("node_type", [ClangASTNode, ClangJsonASTNode])
    def test_make_sure_unused_var_still_run(self, node_type):
        assert_that(
            calling(lambda: remove_unused_variable_low_level(node_type)),
            not_(raises(Exception)),
        )
        assert_that(
            calling(lambda: remove_unused_variable_using_refactor_method(node_type)),
            not_(raises(Exception)),
        )

    def test_make_sure_replace_if_with_ternary_still_run(self):
        result = replace_if_with_ternary()

        assert_that(
            result,
            is_(
                "int a = 1;\n        int b = 2;\n        int c = 3;\n"
                "        int d = 4;\n        void f(){\n            c++; b=(a==1) ? 2:3; d++;\n        }"
            ),
        )


"""

E       Expected: Expected a callable raising <class 'Exception'>
E            but: Correct assertion type raised, but a string containing 
"Error parsing: ClangASTNode1.cpp \n       + errors: 4: 'stddef.h' file not found at
<SourceLocation file '/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/cstddef', line 50, column 10>\n       " not found. 
Exception message was: 
"Error parsing: ClangASTNode1.cpp errors: 4: 'stddef.h' file not found at 
<SourceLocation file '/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/cstddef', line 50, column 10>
E       "
"""
