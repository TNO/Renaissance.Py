
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases nested replacements and multiple patterns.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl.clang import ClangASTNode
from syntax_tree import ASTShower, TextUtils, ASTFinder

example_code = """
void f1(int a, int b, int c);
void f2(int a, int c);
void f(){
    const int a = 1;
    const int b = 2;
    int isAOne = a==1;
    int c = 0, d=0;
    if (a==1) {
        d++;
        if(a==1){
            d++;
            c=d;
            f1(a,b,c);
        }
    }
    if (a==2) {
        c++;
        f1(a,b,c);
    }
    f1(a,b,c);
}
""".strip()

expected_result = """
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
          d++;
          c=d;
          //changed function f1 to f2
          f2(a,c);
       }
    }
    if (a==2) {
        c++;
        //changed function f1 to f2
        f2(a,c);
    }
    //changed function f1 to f2
    f2(a,c);
}
""".strip()



def refactor_with_nested_compositions(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    factory = ASTFactory(ClangASTNode, args if not code else args[1:])
    # Create a pattern factory (using the factory (hence also its args)
    #create translation unit
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'example.c')
    # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
    pattern_factory = CPatternFactory(factory, atu)
    # create a pattern that matches an if statement with a==1 as the condition and a block of statements as the body
    # the type is important so it's declared as const int a
    pattern1 = pattern_factory.create_statements('if(a==1){$$stmts;}', extra_declarations=['const int a;'])
    # for pattern 2 we create a fully functional c snippet with a call to f1
    # note that the f1 declaration is derived from the atu
    pattern2 = pattern_factory.create('int $a,$b,$c; void fff() {f1($a,$b,$c);}')
    ASTShower.show_node(pattern1[0], include_properties=True)

    # we only want to search the call expression as a pattern so it's searched using the kind 
    pattern2 = ASTFinder.find_kind(pattern2, '(?i)Call_?Expr').to_list()

    # the replacement code strip indent is used to be agnostic to the indentation of the replacement 
    pattern1replacement = TextUtils.strip_indent("""
        //changed if expr to const
        if(isAOne){
            $$stmts;
        }""")
    pattern2replacement = '//changed function f1 to f2\nf2($a,$c);'
   
    # show node and patterns enable include properties to show the properties of the nodes
    include_properties = True
    ASTShower.show_node(atu, include_properties)
    ASTShower.show_node(pattern1[0], include_properties)
    ASTShower.show_node(pattern2[0], include_properties)

    result = None
    while atu:
        #create an ASTRewriter
        rewriter = ASTRewriter(atu)
        def raw(nodes):
            res = ''
            for node in nodes:
                res += node.text
            return res + '\n'
        # create a refactoring that use different replacement code for different patterns
        def refactor(match):
            if match.patterns == pattern1:
                replment_text = pattern1replacement
            else:
                replment_text = pattern2replacement

            for repl_snippet in match.expansions:
                replment_text = replment_text.replace(repl_snippet, raw(match.expansions[repl_snippet]))
            return rewriter.replace(replment_text, match.nodes)



        # search matches for pattern1 and pattern2 and replace them using the refactor function
        MatchFinder.find_all(atu.children, pattern1, pattern2).\
            peek(lambda match: print('peek: ' +str(match.get_raw_signatures()))).\
            for_each(refactor)
        
        #print the rewritten code
        result = rewriter.apply_to_string()
        if rewriter.has_changed():
            atu = factory.create_from_text(result, 'example.c')
        else:
            atu = None
    return result

if __name__ == "__main__":
    import sys
    result =  refactor_with_nested_compositions(sys.argv)
    print(result)

