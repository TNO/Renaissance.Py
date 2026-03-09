#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases nested replacements and multiple patterns.
from renaissance.syntax_tree import ASTFactory, MatchFinder, ASTRewriter
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTShower, TextUtils
from renaissance.syntax_tree.match_finder import match_pattern

example_code = """
from module import foo, bar, baz, quux
ba(51)
na(52)
na(53)
pa(54)
if pa():
  ba()
pa(54)  
"""

def python_ast_smoke_test():
    factory = ASTFactory(PythonASTNode)
    atu = factory.create_from_text(example_code, 'test.py')
    pattern_factory = PythonPatternFactory(factory, atu)

    pattern1 = pattern_factory.create_statements('if pa(): $$stmts')
    pattern2 = pattern_factory.create_expression('na($a)')

    ASTShower.show_node(pattern1[0], include_properties=True)

    pattern1replacement = TextUtils.strip_indent("""
            # changed if expr to const
            isAOne=True
            if(isAOne):
                $$stmts
            """)
    pattern2replacement = '# changed function f1 to f2\nf2($a,123456)\n'

    rewriter = ASTRewriter(atu)
    for match in match_pattern(atu.children, pattern1):
        refactor(match,pattern1replacement , rewriter)
    for match in match_pattern(atu.children, [pattern2]):
        refactor(match,pattern2replacement , rewriter)
    return rewriter.apply_to_string()

def raw(nodes):
    res = ''
    for node in nodes:
        res += node.text
    return res + '\n'

# create a refactoring that use different replacement code for different patterns
def refactor(match,replment_text, rewriter):
    for repl_snippet in match.expansions:
        replment_text = replment_text.replace(repl_snippet, raw(match.expansions[repl_snippet]))
    return rewriter.replace(replment_text, match.nodes)


if __name__ == "__main__":

    result = python_ast_smoke_test()
    print(result)

