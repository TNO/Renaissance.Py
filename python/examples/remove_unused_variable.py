# This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
# It specifically showcases the replacement of if-else statements with ternary operators.
from refactoring import CleanupRefactoring
from syntax_tree import ASTFactory, ASTFinder, ASTRewriter, ASTShower, ASTProcessor, ASTNode
from impl import ClangJsonASTNode, ClangASTNode

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


def remove_unused_variable_using_refactor_method(node_type: type[ASTNode]):
    factory = ASTFactory(node_type, [])
    # create translation unit
    atu = factory.create_from_text(example_code, "test.c")
    # create a Refactor
    refactor = ASTProcessor(atu, factory, in_memory=True)

    CleanupRefactoring.remove_unused_variables(refactor)
    result = refactor.apply_to_string().strip()
    # print the rewritten code
    print(f"Using cleanup refactoring results {node_type.__name__}:")
    print(result)

    return result, expected_result_refactor


def remove_unused_variable_low_level(node_type: type[ASTNode]):
    factory = ASTFactory(ClangJsonASTNode, [])
    # Create a pattern factory (using the factory (hence also its args)
    # create translation unit
    atu = factory.create_from_text(example_code, "test.c")

    # create an ASTRewriter
    rewriter = ASTRewriter(atu)

    ASTShower.show_node(atu)
    # search matches and replace them
    ASTFinder.find_kind(atu, "(?i)Compound?Stmt").flat_map(
        lambda func: ASTFinder.find_kind(func, "(?i)Var_?Decl")
    ).filter(lambda node: len(node.referenced_by) == 0).map(
        lambda node: node.parent
    ).for_each(
        lambda node: rewriter.remove(node, True, True)
    )

    # print the rewritten code
    print(f"Low level results using {node_type.__name__}:")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_refactor


if __name__ == "__main__":
    import sys

    for node_type in [ClangASTNode, ClangJsonASTNode]:
        remove_unused_variable_low_level(node_type)
        remove_unused_variable_using_refactor_method(node_type)
