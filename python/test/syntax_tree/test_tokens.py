import io
import tokenize

code = """
# Python 3: Fibonacci series up to n
def fib(n):
    [a, b] = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a+b
    print()
fib(1000)
"""

# tokens = tokenize.generate_tokens(io.StringIO(code).readline)

# for tok in tokens:
#     print(tok.type, tokenize.tok_name[tok.type], repr(tok.string), tok.start, tok.end)

import ast

try:
    tree = ast.parse(code)

    for node in ast.walk(tree):
        # if isinstance(node, ast.If):
        #     print("If statement at", node.lineno, ":", node.col_offset)
        #     print("test:\t\t", node)
        #     print("cond:\t\t", node.test)
        #     print(type(node.test))
        #     print("body:\t\t", node.body)
        #     print(type(node.body))
        #     print("orelse:\t\t", node.orelse)
        #     print(type(node.orelse))
        # if isinstance(node, ast.FunctionDef):
        #     print("Function at ", node.lineno, ":", node.col_offset)
        #     print("node:\t\t", node)
        #     print("name:\t\t", node.name)
        #     print(type(node.name))
        #     print("args:\t\t", node.args)
        #     print(type(node.args))
        #     print("body:\t\t", node.body)
        #     print(type(node.body))
        #     print("decorator_list:\t", node.decorator_list)
        #     print("returns:\t", node.returns)
        #     print("type_comment:\t", node.type_comment)
        #     print("type_params:\t", node.type_params)
        # if isinstance(node, ast.Call):
        #     print("Call at", getattr(node, "lineno", "?"), ":", getattr(node, "col_offset", "?") ,"->", ast.unparse(node))
        if isinstance(node,ast.Assign):
            # note that unparse is NOT equal to the original text.
            # e.g. a, b = 0, 1 is unparsed as a, b = (0, 1)
            print("Assign at", node.lineno, ":", node.col_offset, ast.unparse(node))
            print(node)
        

except SyntaxError as e:
    print("SyntaxError:", e.msg)
    print("Line:", e.lineno, "Offset:", e.offset)
    print("Text:", e.text.rstrip() if e.text else None)
