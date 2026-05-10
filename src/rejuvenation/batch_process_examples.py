# use clang to load and walk a compilation database
import textwrap
from dataclasses import dataclass
from typing import Callable
from renaissance.syntax_tree.recipe_ast_processor import (
    RecipeASTProcessor,
    after_step,
    recipe_step,
    final_action,
)
from typing_extensions import Iterable
from renaissance.impl.clang import ClangASTNode
from renaissance.impl.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.refactoring import CleanupRefactoring
from renaissance.syntax_tree import (
    ASTProcessor,
    ASTNode,
    TextUtils,
    ASTFactory,
    BatchASTProcessor,
)

example_1 = textwrap.dedent("""
        void x(int a) {}
        void x1(int a) {}
        void x2(int a) {}

        void f1(int a){
            int unused = 0;
            int unused2 = 0; //must be removed
            if (a==1) {
                int unused = 0;
                int unused2 = 0; //should be kept
                int c = unused2;
                x1(c);
            }
        }
        """)

example_2 = textwrap.dedent("""
        void x(int a) {}
        void x1(int a) {}
        void x2(int a) {}
        void f2(int a){
            int unused = 0;
            if (a==1) {
                int unused = 0;
                int another_unused = 0;
                int used2 = 0; //should be kept
                int c = used2;
                x2(c);
            }
        }
        """)


# generate a simple code base provider in real life use a compilation database
def simple_codebase_provider() -> Iterable[tuple[ASTFactory, ASTNode]]:
    for impl_type in [ClangASTNode, ClangJsonASTNode]:
        factory = ASTFactory(impl_type)
        atu1 = factory.create_from_text(example_1, impl_type.__name__ + "1.c")
        yield factory, atu1
        atu2 = factory.create_from_text(example_2, impl_type.__name__ + "2.c")
        yield factory, atu2


def print_results(title, batch_processor):
    print(title + ":")
    for file, code in batch_processor.in_memory_files.items():
        print(TextUtils.shift_right(file, 4) + "\n")
        print(TextUtils.shift_right(code, 8) + "\n")


def batch_remove_unused_variable_once_example():
    """
    This function demonstrates a batch processing example using different AST node implementations.
    It iterates over a list of AST node implementations (`ClangASTNode` and `ClangJsonASTNode`),
    and for each implementation, it generates a codebase provider that yields tuples of
    `ASTFactory` and `ASTNode` created from example source texts (`example_1` and `example_2`).
    The function then creates a `BatchASTProcessor` with in-memory storage enabled and processes
    the codebase using the `CleanupRefactoring.remove_unused_variables` refactoring operation.
    Finally, it prints the rewritten code stored in memory.
    """
    # generate a batch processor for testing purposes we store into memory
    batch_processor = BatchASTProcessor(in_memory=True)
    batch_processor.once(simple_codebase_provider, CleanupRefactoring.remove_unused_variables)
    # print the rewritten code normally you would write to a file
    print_results("example batch remove unused variable once", batch_processor)


def batch_repeat_example():
    """
    Demonstrates the use of a batch processor to perform multiple refactoring operations on a codebase.
    This example creates an in-memory batch processor and applies two refactoring operations:
    1. CleanupRefactoring.remove_unused_variables: Removes unused variables from the codebase.
    2. remove_function: Removes all function calls from the codebase.
    The results of the refactoring operations are printed to the console.

    Repeat is in action here:
        the first time the codebase is processed, the unused variables are removed.
        and the function calls are removed.
        the second time the codebase is processed, the new unused variables are removed again.
    Note:
        In a real-world scenario, the rewritten code would typically be written to a file instead of being printed.
    """
    # generate a batch processor for testing purposes we store into memory
    batch_processor = BatchASTProcessor(in_memory=True)

    # remove a function to create more unused variables
    def remove_function(ast_processor: ASTProcessor):
        [ast_processor.insert_before("// ", node, False, False) for node in ast_processor.find_ast_type(Call)]

    # batch_processor.repeat(simple_codebase_provider, [remove_function])
    batch_processor.repeat(
        simple_codebase_provider,
        [CleanupRefactoring.remove_unused_variables, remove_function],
    )
    # print the rewritten code normally you would write to a file
    print_results("example batch repeat", batch_processor)


@dataclass
class Call:
    callee: str
    calls: str


class AnalysisRecipe:
    def __init__(self):
        self._calls = []

    @recipe_step(order=0)
    def store_function_call(self, ast_processor: ASTProcessor) -> Callable[[], None] | None:
        # find all function calls and store them, this routing is invoked in parallel!
        calls = []
        [AnalysisRecipe._add_function_call(node, calls) for node in ast_processor.find_ast_type(Call)]
        # the resulting lambda is invoked single threaded
        # this kind of mechanism is mainly used to store results from multiple processors
        # for refactoring operations this is not needed as a refactoring operation is single threaded
        if calls:
            return lambda: self._calls.extend(calls)
        return None
    @after_step("store_function_call")
    def just_show_the_method(self):
        print("called after store_function_call")

    @final_action()
    def final_action(self):
        print("Calls:")
        for call in self._calls:
            print("    " + call.callee + " --  calls --> " + call.calls)

    @staticmethod
    def _add_function_call(call: ASTNode, calls: list[Call]):
        callee = call.get_ancestor("(?i)Function_?Decl")
        if callee:
            calls.append(Call(callee.name, call.children[0].name))


def batch_recipe_example():
    print("example batch analysis using recipe:\n")
    recipe_ast_processor = RecipeASTProcessor(AnalysisRecipe(), simple_codebase_provider, r".*", in_memory=True)
    recipe_ast_processor.run()


if __name__ == "__main__":
    # a list of example to show batch processing of a code base
    batch_remove_unused_variable_once_example()
    batch_repeat_example()
    batch_recipe_example()
