
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases the replacement of if-else statements with ternary operators.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl.clang import ClangASTNode

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


def main(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    factory = ASTFactory(ClangASTNode, args if not code else args[1:])
    # Create a pattern factory (using the factory (hence also its args)
    pattern_factory = CPatternFactory(factory)
    patterns = pattern_factory.create_statements('if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}')

    #create translation unit
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')
    #create an ASTRewriter
    rewriter = ASTRewriter(atu)
    # search matches and replace them
    MatchFinder.find_all(atu, patterns).for_each(lambda match: rewriter.replace('$$before; b=($exp) ? $d1:$d2; $$after;',match))
    #print the rewritten code
    print(rewriter.apply_to_string())

if __name__ == "__main__":
    import sys
    main(sys.argv)