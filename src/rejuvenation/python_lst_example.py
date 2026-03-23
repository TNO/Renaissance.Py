import tree_sitter_python as tspython

from renaissance.impl import MATCH_ONE
from renaissance.impl.tree_sitter_adapter import TreeSitterAdapter, TsPatternFactory
from renaissance.syntax_tree import ASTShower, ASTFinder, ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern


def python_lst_smoke_test():

    code = """
    def greet(name):
        print("Hello", name)
    
    if True:
        greet("World")
    """
    adapter = TreeSitterAdapter(tspython)
    tree = adapter.parse_code(code)
    lst = adapter.to_lst(code, tree)

    # Show the root of the LST
    ASTShower.show_node(lst.root)

    nodes = ASTFinder.find_kind(lst.root, "identifier")

    ASTShower.show_node(nodes[0])

    pattern_factory = TsPatternFactory(adapter)

    pattern = pattern_factory.create_statements("$greet($arg)")

    matches = match_pattern(lst.root.children, pattern)

    ASTShower.show_node(matches[0].nodes[0])
    rewriter = ASTRewriter(lst.root)

    def raw(nodes):
        res = ""
        for node in nodes:
            if isinstance(node, str):
                res += node
            else:
                res += node.signature
        return res + "\n"

    for match in matches:
        replment_text = "my_awesome_$greet($arg,'is','awesome)"
        for repl_snippet in match.expansions:
            replment_text = replment_text.replace(
                repl_snippet.replace(MATCH_ONE, "$"),
                raw(match.expansions[repl_snippet]),
            )
        rewriter.replace(replment_text, match.nodes)
    result = rewriter.apply_to_string()
    print(result)

    def add_children(parent):
        my_uml = ""
        for child in parent.children:
            my_uml += f'"{parent.kind}"->"{child.kind}"\n'
            my_uml += add_children(child)
        return my_uml

    uml = add_children(lst.root)
    print(uml)

    # if rewriter.has_changed():
    #     atu = factory.create_from_text(result, 'test.py')
    # else:
    #     atu = None
    return result
