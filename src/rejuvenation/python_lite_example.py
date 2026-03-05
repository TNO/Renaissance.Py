import ast

import renaissance.impl.python.python_lite_ast_node
from renaissance.syntax_tree import ASTShower, ASTFinder

code = """
def greet(name):
    print("Hello", name)

if True:
    greet("World")
"""
root = ast.parse(code)
ASTShower.show_node(root)
print(ast.dump(root))

nodes=ASTFinder.find_kind(root, "If").to_list()

ASTShower.show_node(nodes[0])
#
# pattern_factory = TsPatternFactory(adapter)
#
# pattern = pattern_factory.create_statements("$greet($arg)")
#
# matches=match_pattern(lst.root.children, pattern)
#
# ASTShower.show_node(matches[0].nodes[0])
# rewriter = ASTRewriter(lst.root)
#
#
# def raw(nodes):
#     res = ''
#     for node in nodes:
#         if isinstance(node,str ):
#             res += node
#         else:
#             res += node.signature
#     return res + '\n'
#
# for match in matches:
#     replment_text = "my_awesome_$greet($arg,'is','awesome)"
#     for repl_snippet in match.expansions:
#         replment_text = replment_text.replace(repl_snippet.replace(MATCH_ONE,'$'), raw(match.expansions[repl_snippet]))
#     rewriter.replace(replment_text, match.nodes)
# result = rewriter.apply_to_string()
# print(result)
#
# def add_children(parent):
#     uml =""
#     for child in parent.children:
#         uml += f'"{parent.kind}"->"{child.kind}"\n'
#         uml +=add_children(child)
#     return uml
#
# uml = add_children( lst.root)
# print(uml)
#
# # if rewriter.has_changed():
# #     atu = factory.create_from_text(result, 'test.py')
# # else:
# #     atu = None
