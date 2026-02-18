import ast

from impl.python import PythonASTNode


def test_it_can_be_created():
    it = PythonASTNode(ast.Pass())
    assert it

def test_it_has_elements():
    it = PythonASTNode(ast.parse('def fun():  pass'))
    assert it[0]==it.children[0]

# def test_it_has_key_pairs():
#     it = PythonASTNode(ast.parse('def fun():  pass'))
#     assert it['name']==it.properties['name']
