import ast
import unittest
from _ast import AST
from typing import Sequence

from parameterized import parameterized

from impl import PythonASTNode, PythonPatternFactory, ClangASTNode
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder, ASTShower


def walk(node):
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(node.get_children())
        yield node


ALL_SYNTAX = '''
a = 3
# long_expression = component_one + component_two + component_three + component_four + component_five + component_six
# 
# 
# def xyzzy(a1, a2,
#           long_parameter_1,
#           a3, a4,
#           long_parameter_2):
#     pass
# 
# 
# xyzzy(1, 2,
#       'long_string_constant1',
#       3, 4,
#       'long_string_constant2')
# 
# xyzzy(
#     'with',
#     'hanging',
#     'indent'
# )
# attrs = [e.attr for e in
#          items]
# 
# num_dict = {"one": 1,
#             "two": 2,
#             "three": 3,
#             "four": 4,
#             "five": 5}
# 
# colors = ['red', 'green',
#           'blue', 'black',
#           'white', 'gray']
# 
# star_names = {"Sirius",
#               "Betelgeuse",
#               "Polaris",
#               "Vega",
#               "Arcturus",
#               "Aldebaran"}
# 
# planets = ("Mercury", "Venus",
#            "Earth", "Mars",
#            "Jupiter",
#            "Saturn", "Uranus",
#            "Neptune")
# 
# ingredients = [
#     'green',
#     'eggs',
# ]
# 
# if True: pass
# 
# try:
#     pass
# finally:
#     pass
'''

class PythonNodeTest(unittest.TestCase):
    def setUp(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text(ALL_SYNTAX, 'all.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    def test_Add(self):
        simple = self.pattern_factory.create('True and False')
        it = simple.get_children()[0].get_children()[0]
        result = ASTShower.get_node(it)
        self.assertEqual('(And, , None[0:0]): ||\n', result)
        self.assertEqual('And', it.get_kind())
        # self.assertEqual('And', it.get_raw_signature())

    @parameterized.expand([
        ('i:int=0', 'AnnAssign'),
        ('assert 0', 'Assert'),
        ('async for f in fs:  pass', 'AsyncFor'),
        ('async def fun(): pass', 'AsyncFunctionDef'),
        ('async with open("x"): pass' ,'AsyncWith'),
        ('x += 5','AugAssign'),
        ('break','Break'),
        ('class x:pass','ClassDef'),
        ('continue', 'Continue'),
        ('import x',   'Import'),
        ('from x import y',   'ImportFrom'),
        ('match x:\n  case _:    pass',   'Match'),
        ('pass',   'Pass'),
        ('raise',   'Raise'),
        ('return',   'Return'),
        ('try:\n  pass\nfinally:\n  pass',   'Try'),
        ('try:\n  x()\nexcept* e:\n  pass','TryStar'),
        ('while True: pass',   'While'),
    ])
    def test_stmt_kind(self, raw, kind):
        it = self.pattern_factory.create(raw)
        result = ASTShower.get_node(it)
        self.assertEqual(kind, it.get_kind())

    # ('with', 'With'),
    # ('await (fun(2))', 'Await'),
    # ('True and False', 'BinOp'),

    # ('0x01 and 0x10', 'BitAnd'''),
    # ('0x01 or 0x10', 'BitOr'),
    # ('0x01 xor 0x10', 'BitXor'),
    # ('', 'BoolOp'),

    # ('global x', 'Global'),

    # ('non local x = 0', 'Nonlocal'),

    # ('delete', 'Delete'),
    #
    # ('y as x', 'TypeAlias'),
    #
    # # Code with nonlocal statement
    code = """
    
    """
    # tree = ast.parse(code)


    # for node in ast.walk(tree):
    #     if isinstance(node, ast.Nonlocal):
    #         print(f"Found Nonlocal node with names: {node.names}")

    @parameterized.expand([
        ('''
def outer():
    x = 10
    y = 20
    
    def inner():
        nonlocal x, y
    #     x += 5
    # return inner()
''', 'NonLocal'),
    ])
    def test_stmt_kind_in_context(self, raw, kind):
        it = self.factory.create_from_text(raw,'context.py')
        kinds = [node.get_kind() for node in walk(it)]
        self.assertIn(kind,kinds)



    #     ast.Call:
    #     return isinstance(other, type(node)) and match_call(node, other)
    #
    #
    # def test_ast.Compare:
    # def test_pass
    # def test_ast.Constant:
    # def test_return isinstance(other, type(node)) and match(node.value, other.value)


    # def test_Dict(__ast.expr):
    # def test_DictComp(__ast.expr):
    # def test_Div(__ast.operator):
    # def test_Eq(__ast.cmpop):
    # def test_ExceptHandler(__ast.excepthandler):
    # def test_Expr:
    #     return isinstance(other, type(node)) and match(node.value, other.value)
    # def test_Expression(__ast.mod):
    # def test_FloorDiv(__ast.operator):
    # def test_For(__ast.stmt):
    # def test_FormattedValue(__ast.expr):
    # def test_FunctionType(__ast.mod):
    # def test_GeneratorExp(__ast.expr):
    # def test_In(__ast.cmpop):
    # def test_Interactive(__ast.mod):
    # def test_Invert(__ast.unaryop):
    # def test_Is(__ast.cmpop):
    # def test_IsNot(__ast.cmpop):
    # def test_JoinedStr(__ast.expr):
    # def test_LShift(__ast.operator):
    # def test_Lambda(__ast.expr):
    # def test_List(__ast.expr):
    # def test_ListComp(__ast.expr):
    # def test_Load(__ast.expr_context):
    # def test_Lt(__ast.cmpop):
    # def test_LtE(__ast.cmpop):
    # def test_MatMult(__ast.operator):
    # def test_FunctionDef(__ast.stmt):
    # def test_MatchAs(__ast.pattern):
    # def test_MatchClass(__ast.pattern):
    # def test_MatchMapping(__ast.pattern):
    # def test_MatchOr(__ast.pattern):
    # def test_MatchSequence(__ast.pattern):
    # def test_MatchSingleton(__ast.pattern):
    # def test_MatchStar(__ast.pattern):
    # def test_MatchValue(__ast.pattern):
    # def test_Mod(__ast.operator):
    # def test_Module(__ast.mod):
    # def test_Mult(__ast.operator):
    # def test_Name(self):
    #     return isinstance(other, type(node)) and match(node.id, other.id)
    # def test_NamedExpr(__ast.expr):
    # def test_Not(__ast.unaryop):
    # def test_NotEq(__ast.cmpop):
    # def test_NotIn(__ast.cmpop):
    # def test_Or(__ast.boolop):
    # def test_ParamSpec(__ast.type_param):
    # def test_Pow(__ast.operator):
    # def test_RShift(__ast.operator):
    # def test_Set(__ast.expr):
    # def test_SetComp(__ast.expr):
    # def test_Slice(__ast.expr):
    # def test_Starred(__ast.expr):
    # def test_Store(__ast.expr_context):
    # def test_Sub(__ast.operator):
    # def test_Subscript(__ast.expr):
    # def test_Tuple(__ast.expr):
    # def test_TypeIgnore(__ast.type_ignore):
    # def test_TypeVar(__ast.type_param):
    # def test_TypeVarTuple(__ast.type_param):
    # def test_UAdd(__ast.unaryop):
    # def test_USub(__ast.unaryop):
    # def test_UnaryOp(__ast.expr):
# def test_Gt(__ast.cmpop):
# def test_GtE(__ast.cmpop):
#
# def test_If(self):
# def test_IfExp(__ast.expr):


    # def test_Yield(__ast.expr):
    # def test_YieldFrom(__ast.expr):

    def test_show_call(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'apple.py')
        second_stmt = atu.get_children()[1]
        self.assertEqual(7,second_stmt.get_start_offset())
        self.assertEqual (7, second_stmt.get_length())
        self.assertEqual('apple.py', second_stmt.get_containing_filename())
        self.assertEqual(atu.translation_unit, second_stmt.translation_unit)


    # def test_show_call_btween_c_and_python(self):
    #     c_factory = ASTFactory(ClangASTNode, [])
    #     c_atu = c_factory.create_from_text(' int ba(int);\n int ca(int);\n int lo(int);\n int na(int);\nint main(){\n  ba(55);\n  ca(555);\n  lo(4444);\n  int na=55;\n}\n', 'lila.c')
    #
    #     c_second_stmt = c_atu.get_children()[4].get_children()[1]
    #     p_factory = ASTFactory(PythonASTNode, [])
    #     p_atu = p_factory.create_from_text('def main():\n  ba(55) \n  ca(555) \n  lo(4444) \n  na=55 \n ', 'apple.py')
    #     p_second_stmt = p_atu.get_children()[0].get_children()[1]
    #     self.assertEqual(c_second_stmt.get_start_offset(),p_second_stmt.get_start_offset())
    #     self.assertEqual (c_second_stmt.get_length(), p_second_stmt.get_length())
    #     self.assertEqual (c_second_stmt.get_raw_signature(), p_second_stmt.get_raw_signature())
    #     self.assertEqual (len(c_second_stmt.get_children()), len(p_second_stmt.get_length()))
    #     # self.assertEqual (c_second_stmt.get_length(), p_second_stmt.get_length())



    if __name__ == '__main__':
        unittest.main()
