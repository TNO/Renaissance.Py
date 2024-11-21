
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases the replacement of if-else statements with ternary operators.
from refactoring import CleanupRefactoring
from syntax_tree import ASTFactory, ASTFinder, ASTRewriter, ASTShower, ASTProcessor
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

def remove_unused_variable_using_refactor_method(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    for node_type in [ClangASTNode, ClangJsonASTNode]:
        factory = ASTFactory(ClangJsonASTNode, args if not code else args[1:])
        #create translation unit
        atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')
        #create a Refactor
        refactor = ASTProcessor(atu, factory, {}, in_memory=True)

        CleanupRefactoring.remove_unused_variables(refactor)
        result = refactor.apply_to_string()
        #print the rewritten code
        print (f'Using cleanup refactoring results {node_type.__name__}:')
        print(result)

def remove_unused_variable_low_level(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    for node_type in [ClangASTNode, ClangJsonASTNode]:
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
        print (f'Low level results using {node_type.__name__}:')
        print(rewriter.apply_to_string())

if __name__ == "__main__":
    import sys
    remove_unused_variable_low_level(sys.argv)
    remove_unused_variable_using_refactor_method(sys.argv)