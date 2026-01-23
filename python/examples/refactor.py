import ast

from common import Stream
from impl.python import find_all
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases nested replacements and multiple patterns.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTShower, TextUtils, ASTFinder

example_code = """
from module import foo, bar, baz, quux
ba(51)
na(52)
na(53)
pa(54)
if pa():
  ba()
pa(54)  
""".strip()


def refactor_with_nested_compositions(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ''

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    factory = ASTFactory(PythonASTNode, args if not code else args[1:])
    # Create a pattern factory (using the factory (hence also its args)
    #create translation unit
    atu = factory.create(code) if code else factory.create_from_text(example_code, 'test.py')
    # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
    pattern_factory = PythonPatternFactory(factory, atu)
    pattern1 = pattern_factory.create_statements('if pa(): $$stmts')
    # for pattern 2 we create a fully functional c snippet with a call to f1
    # note that the f1 declaration is derived from the atu
    pattern2 = pattern_factory.create_expression('na($a)')
    ASTShower.show_node(pattern1[0], include_properties=True)

    # the replacement code strip indent is used to be agnostic to the indentation of the replacement
    pattern1replacement = TextUtils.strip_indent("""
            # changed if expr to const
            if(isAOne):
                $$stmts
            """)
    pattern2replacement = '# changed function f1 to f2\nf2($a,c)'

    # show node and patterns enable include properties to show the properties of the nodes
    include_properties = True
    ASTShower.show_node(atu, include_properties)
    ASTShower.show_node(pattern1[0], include_properties)
    ASTShower.show_node(pattern2, include_properties)

    result = None
    while atu:
        # create an ASTRewriter
        rewriter = ASTRewriter(atu)

        # create a refactoring that use different replacement code for different patterns
        def refactor(match):
            if match.patterns == pattern1:
                return rewriter.replace(pattern1replacement, match)
            return rewriter.replace(pattern2replacement, match)

        # search matches for pattern1 and pattern2 and replace them using the refactor function
        MatchFinder.find_all(atu, pattern1, pattern2). \
            peek(lambda match: print('peek: ' + str(match.get_raw_signatures()))). \
            for_each(refactor)

        # print the rewritten code
        result = rewriter.apply_to_string()
        if rewriter.has_changed():
            atu = factory.create_from_text(result, 'test.py')
        else:
            atu = None
    return result


if __name__ == "__main__":
    import sys

    result = refactor_with_nested_compositions(sys.argv)
    print(result)

