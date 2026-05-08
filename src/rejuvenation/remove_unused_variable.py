# This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
# It specifically showcases the replacement of if-else statements with ternary operators.
from more_itertools import flatten

from renaissance.impl.types import VariableDeclaration, CompoundStatement
from renaissance.refactoring import CleanupRefactoring
from renaissance.syntax_tree import (
    ASTFactory,
    ASTRewriter,
    ASTShower,
    ASTProcessor,
    ASTNode,
)
from renaissance.impl.clang import ClangASTNode
from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree.ast_finder import find_ast_type

example_code = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void x(int a) {
        }
        void f(){
            int unused = 0;
            int unused2 = 0; //must be removed
            if (a==1) {
                int unused = 0;
                int unused2 = 0; //should be kept
                int c = unused2;
                x(c);
            }
        }
        """
expected_result_refactor = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void x(int a) {
        }
        void f(){
            if (a==1) {
                int unused2 = 0; //should be kept
                int c = unused2;
                x(c);
            }
        }""".strip()


def remove_unused_variable_using_refactor_method(node_type1: type[ASTNode]):
    factory = ASTFactory(node_type1, [])
    # create translation unit
    atu = factory.create_from_text(example_code, "test.c")
    # create a Refactor
    refactor = ASTProcessor(atu, factory, in_memory=True)

    CleanupRefactoring.remove_unused_variables(refactor)
    result = refactor.apply_to_string().strip()
    # print the rewritten code
    print(f"Using cleanup refactoring results {node_type1.__name__}:")
    print(result)

    return result, expected_result_refactor


def remove_unused_variable_low_level(node_type1: type[ASTNode]):
    factory = ASTFactory(ClangJsonASTNode, [])
    # Create a pattern factory (using the factory (hence also its args)
    # create translation unit
    atu = factory.create_from_text(example_code, "test.c")

    # create an ASTRewriter
    rewriter = ASTRewriter(atu)

    ASTShower.show_node(atu)
    # search matches and replace them
    funcs = flatten(find_ast_type(func, VariableDeclaration) for func in (find_ast_type(atu, CompoundStatement)))
    [rewriter.remove(node.parent, True, True) for node in funcs if len(node.referenced_by) == 0]

    # print the rewritten code
    print(f"Low level results using {node_type1.__name__}:")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_refactor


if __name__ == "__main__":

    for node_type in [ClangASTNode, ClangJsonASTNode]:
        remove_unused_variable_low_level(node_type)
        remove_unused_variable_using_refactor_method(node_type)
