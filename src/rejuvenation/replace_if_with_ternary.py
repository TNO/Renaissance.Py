# This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
# It specifically showcases the replacement of if-else statements with ternary operators.
from renaissance.syntax_tree import ASTFactory, MatchFinder, ASTRewriter
from renaissance.impl.clang import ClangASTNode, CPatternFactory

example_code = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void f(){
            if (a==1) {
                c++;
                b = 2;
                d++;
            }
            else {
                c++;
                b = 3;
                d++;
            }
        }
        """

expected_result = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void f(){
            c++; b=(a==1) ? 2:3; d++;
        }
        """.strip()


def replace_if_with_ternary():
    """
    Replaces if-else statements in the given C code with ternary operator expressions.
    This function performs the following steps:
    1. Creates an AST factory with the specified arguments.
    2. Creates a pattern factory using the AST factory.
    3. Defines a pattern for if-else statements.
    4. Creates a translation unit from the provided example code.
    5. Initializes an AST rewriter for the translation unit.
    6. Searches for matches of the if-else pattern in the translation unit.
    7. Replaces matched if-else statements with ternary operator expressions.
    8. Returns the rewritten code as a string.
    Returns:
        str: The rewritten C code with if-else statements replaced by ternary operators.
    """

    # Create a factory with arguments from the command line, for example, -I/usr/include
    factory = ASTFactory(ClangASTNode, [])
    # Create a pattern factory (using the factory (hence also its args)
    pattern_factory = CPatternFactory(factory)
    if_else_patterns = pattern_factory.create_statements("if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}")

    # Create translation unit
    atu = factory.create_from_text(example_code, "test.c")
    # Create an ASTRewriter
    rewriter = ASTRewriter(atu)
    # Search matches and replace them
    (rewriter.replace("$$before; b=($exp) ? $d1:$d2; $$after;", match)
     for match in MatchFinder.find_all(atu.children, if_else_patterns))
    # Return the rewritten code
    return rewriter.apply_to_string().strip()


if __name__ == "__main__":

    result = replace_if_with_ternary()
    print(result)
