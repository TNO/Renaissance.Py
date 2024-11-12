
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases the replacement of if-else statements with ternary operators.
from syntax_tree import ASTFactory, ASTFinder, ASTRewriter, ASTShower
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


def main(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    for node_type in [ClangASTNode, ClangJsonASTNode]:
        print (f'Using {node_type.__name__}')
        factory = ASTFactory(ClangJsonASTNode, args if not code else args[1:])
        # Create a pattern factory (using the factory (hence also its args)
        #create translation unit
        atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')

        #create an ASTRewriter
        rewriter = ASTRewriter(atu)

        ASTShower.show_node(atu)
        # search matches and replace them
        ASTFinder.find_kind(atu, '(?i)Compound?Stmt').\
            flat_map(lambda func: ASTFinder.find_kind(func,'(?i)Var_?Decl')).\
            filter(lambda node: len(node.get_referenced_by())==0).\
            map(lambda node: node.get_parent()).\
            for_each(lambda node: rewriter.remove(node, True, True))
            
        #print the rewritten code
        print (f'Results using {node_type.__name__}:')
        print(rewriter.apply_to_string())

if __name__ == "__main__":
    import sys
    main(sys.argv)