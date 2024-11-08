
#This script demonstrates various techniques for refactoring C code using an abstract syntax tree (AST) approach.
#It showcases how to add comments, replace types, and find specific nodes in the AST using different methods.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter, ASTUtils, ASTShower, ASTFinder
from impl.clang import ClangASTNode

example_code = """
    typedef int fancy_new;
    typedef int old;
    void f(){
        int a = 1;
        old b = 2;
        int c = 3;
        old d = 4;
        old e;
    }
    """

def example_add_comment_and_commit(factory, pattern_factory, code):
    # create a pattern that matches the declaration of old 
    # please note that we need to help by telling the old is a type and $value is a variable
    patterns = pattern_factory.create_declarations('old $name = $value;old $name;', extra_declarations=['typedef int old;'], parameters=['$value'])
    #put the pattern in a matrix because we want to find both statements in one go and not a sequence
    patterns_list =[[p] for p in patterns] 

    ASTShower.show_node(patterns[0])
    # if you want to find both statements in one go, you should pass a list of patterns
    # if you don't do that that a sequence of the patterns is searched for

    #create translation unit
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')

    ASTShower.show_node(atu)

    #create an ASTRewriter
    rewriter = ASTRewriter(atu)
    # search matches and replace them
    MatchFinder.find_all(atu, *patterns_list).\
        for_each(lambda match: rewriter.insert_before('// old has become obsolete',match))
    
    #commit
    atu, rewriter = ASTUtils.commit(rewriter, factory, in_memory=True)
    
    # look at the print that marks all old declarations with the provided comment
    print('results after adding comments to the obsolete types:')
    print(atu.get_raw_signature())

def example_replace_old_by_fancy_new(factory, pattern_factory, code):
    # using some different techniques to show the possibilities of map and filter
    patterns = pattern_factory.create_declarations('$old $name = $value;$old $name;', extra_declarations=['typedef int $old;'], parameters=['$value'])
    #put the pattern in a matrix because we want to find separate statements in one go and not the sequence
    patterns_list =[[p] for p in patterns] 

    # a example of how to use a function iso of lambda to filter the nodes
    def matches_old(node):
        if node.get_name() == 'old':
            return True
        return False
    
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')
    rewriter = ASTRewriter(atu)

    MatchFinder.find_all(atu, *patterns_list).\
        map(lambda match: match.get_nodes()['$old'][0]).\
        filter(matches_old).\
        for_each(lambda node: rewriter.replace('fancy_new',node))
    print('results after replacing the old type by fancy_new using MatchFinder:')
    print(rewriter.apply_to_string())

def example_use_ast_kind_finder(factory, pattern_factory, code):
    # Create the translation unit from the provided code or example code
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')
    # Create an ASTRewriter for the translation unit
    rewriter = ASTRewriter(atu)

    # Find all nodes of kind TYPE_REF (case insensitive) and filter those with name 'old'
    ASTFinder.find_kind(atu, '(?i)TYPE.?REF').\
        filter(lambda node: node.get_name()=='old').\
        for_each(lambda node: rewriter.replace('fancy_new', node))
    
    # Print the results after replacing the old type by fancy_new
    print('results after replacing the old type by fancy_new using ASTFinder.find_kind')
    print(rewriter.apply_to_string())

def example_use_ast_function_finder(factory, pattern_factory, code):
    # Create the translation unit from the provided code or example code
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.c')
    # Create an ASTRewriter for the translation unit
    rewriter = ASTRewriter(atu)

    # Define a match function to find nodes of kind TYPE_REF with name 'old'
    def match(node):
        if node.get_kind() == 'TYPE_REF' and node.get_name() == 'old':
            yield node

    # Use ASTFinder to find all matching nodes and replace 'old' with 'fancy_new'
    ASTFinder.find_all(atu, match).\
        for_each(lambda node: rewriter.replace('fancy_new', node))
    
    # Print the results after replacing the old type by fancy_new
    print('results after replacing the old type by fancy_new using ASTFinder.find_all')
    print(rewriter.apply_to_string())



def main(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    factory = ASTFactory(ClangASTNode, args if not code else args[1:])
    # Create a pattern factory (using the factory (hence also its args)
    pattern_factory = CPatternFactory(factory)
    
    example_add_comment_and_commit(factory, pattern_factory, code)
    example_replace_old_by_fancy_new(factory, pattern_factory, code)
    example_use_ast_kind_finder(factory, pattern_factory, code)
    example_use_ast_function_finder(factory, pattern_factory, code)

if __name__ == "__main__":
    import sys
    main(sys.argv)