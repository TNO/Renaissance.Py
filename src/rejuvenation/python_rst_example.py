import ast
import renaissance.impl.python.python_rst_node
from renaissance.syntax_tree import ASTShower, ASTFinder, ASTRewriter
from renaissance.utils.node_util import replace_dollar

# def add_children(parent):
#     uml =""
#     for child in parent.children:
#         uml += f'"{parent.kind}"->"{child.kind}"\n'
#         uml +=add_children(child)
#     return uml
#
#
# def raw(nodes):
#     res = ''
#     for node in nodes:
#         if isinstance(node, str):
#             res += node
#         else:
#             res += node.signature
#     return res + '\n'
#


def python_rst_smoke_test():
    code = """

def greet(name):
    print("Hello", name)

if True:
    greet("World")
    """
    root = ast.parse(code)
    ASTShower.show_node(root)

    nodes = ASTFinder.find_kind(root, "If")

    ASTShower.show_node(nodes[0])

    pattern = ast.parse(replace_dollar("$greet($arg)")).body

    # matches=match_pattern(root.children, pattern)

    # ASTShower.show_node(matches[0].nodes[0])
    # rewriter = ASTRewriter(root)
    #
    #
    #
    # for match in matches:
    #     replment_text = "my_awesome_$greet($arg,'is','awesome)"
    #     for repl_snippet in match.expansions:
    #         replment_text = replment_text.replace(repl_snippet.replace(MATCH_ONE,'$'), raw(match.expansions[repl_snippet]))
    #     rewriter.replace(replment_text, match.nodes)
    # result = rewriter.apply_to_string()
    # print(result)
    #
    #
    # uml = add_children(root)
    # print(uml)

    return ""  # result
