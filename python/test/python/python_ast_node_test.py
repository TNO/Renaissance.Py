import ast
import unittest
from parameterized import parameterized
from impl import PythonASTNode, PythonPatternFactory, ClangASTNode
from syntax_tree import ASTFactory, MatchFinder, ASTShower


def walk(node):
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(node.children)
        yield node


class PythonNodeTest(unittest.TestCase):
    def setUp(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('a = 0', 'all.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    @parameterized.expand([
        ('i:int=0', 'AnnAssign'),
        ('assert 0', 'Assert'),
        ('async for f in fs:  pass', 'AsyncFor'),
        ('async def fun(): pass', 'AsyncFunctionDef'),
        ('async with open("x"): pass', 'AsyncWith'),
        ('x += 5', 'AugAssign'),
        ('break', 'Break'),
        ('class x:pass', 'ClassDef'),
        ('continue', 'Continue'),
        ('fun()', 'Expr'),
        ('def fun(): pass', 'FunctionDef'),
        ('for i in items: pass', 'For'),
        ('import x', 'Import'),
        ('if True: pass', 'If'),
        ('from x import y', 'ImportFrom'),
        ('match x:\n  case _:    pass', 'Match'),
        ('pass', 'Pass'),
        ('raise', 'Raise'),
        ('return', 'Return'),
        ('try:\n  pass\nfinally:\n  pass', 'Try'),
        ('try:\n  x()\nexcept* e:\n  pass', 'TryStar'),
        ('while True: pass', 'While'),
    ])
    def test_stmt_kind(self, raw, kind):
        it = self.pattern_factory.create(raw)
        result = ASTShower.get_node(it)
        self.assertEqual(kind, it.kind)

    @parameterized.expand([
        ('with open() as c: pass', 'With'),
        ('await (fun(2))', 'Await'),
        ('a = 5 + 3', 'BinOp'),

        ('0x01 & 0x10', 'BitAnd'''),
        ('0x01 | 0x10', 'BitOr'),
        ('0x01 ^ 0x10', 'BitXor'),
        ('True and False', 'BoolOp'),
        ('global x', 'Global'),
        ('del x', 'Delete'),

        ('type UserId = int', 'TypeAlias'),
        ('''
def outer():
    x = 10
    y = 20
    def inner():
        nonlocal x, y
        x += 5
    return inner()
''', 'Nonlocal'),

    ])
    def test_stmt_kind_in_context(self, raw, kind):
        it = self.factory.create_from_text(raw, 'context.py')
        kinds = [node.kind for node in walk(it)]
        self.assertIn(kind, kinds)

    @parameterized.expand([
        ('fun()', 'Call'),
        ('{one: 1, two:2}', 'Dict'),
        ('{1,2}', 'Set'),
        ('[1, 2]', 'List'),
        ('{word: len(word) for word in ["one","two"]}', 'DictComp'),
        ('[ n*3 for n in [1, 2]]', 'ListComp'),
        ('{ n*3 for n in [1, 2]}', 'SetComp'),
        ('lambda: fun()', 'Lambda'),
        ('x = (n*2 for n in[1,2])', 'GeneratorExp'),
        ('f"{one}two"', 'JoinedStr'),
        ('items[1:4]', 'Subscript'),
        ('(9, 10)', 'Tuple'),
        ('x = not True', 'UnaryOp'),
        ('yield fun', 'Yield'),
        ('yield from [1,2]', 'YieldFrom'),
        ('x = z if z>y else y', 'IfExp'),

    ])
    def test_expr_kind(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        result = ASTShower.get_node(it)
        self.assertEqual(kind, it.kind)

    def test_Slice(self):
        it = self.pattern_factory.create_expression('items[1:2:3]')
        result = ASTShower.get_node(it)
        self.assertEqual('Slice', it.children[1].kind)

    def test_NamedExpr(self):
        it = self.pattern_factory.create('if n:= len(items): pass')
        result = ASTShower.get_node(it)
        self.assertEqual('NamedExpr', it.children[0].kind)

    def test_Starred(self):
        it = self.pattern_factory.create('*x =[1,2]')
        result = ASTShower.show_node(it)
        self.assertEqual('Starred', it.children[0].children[0].kind)

    def test_FormattedValue(self):
        it = self.pattern_factory.create_expression('f"{one}two"')
        result = ASTShower.show_node(it)
        self.assertEqual('FormattedValue', it.children[0].children[0].kind)

    def test_ExceptHandler(self):
        it = self.pattern_factory.create('try: pass\nexcept NameError:pass')
        result = ASTShower.show_node(it)
        self.assertEqual('ExceptHandler', it.children[1].children[0].kind)

    @parameterized.expand([
        ('a == b', 'Eq'),
        ('a in b', 'In'),
        ('a is b', 'Is'),
        ('a is not b', 'IsNot'),
        ('a < b', 'Lt'),
        ('a <=b', 'LtE'),
        ('a != b', 'NotEq'),
        ('a not in b', 'NotIn'),
        ('a > b', 'Gt'),
        ('a >= b', 'GtE'),
    ])
    def test_comperator_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        self.assertEqual(kind, it.children[1].children[0].kind)

    @parameterized.expand([
        ('case None: return "No data"', 'MatchSingleton'),
        ('case True | False:        return "Boolean value"', 'MatchOr'),
        ('case int(x) if x > 0:        return f"Positive integer: {x}"', 'MatchClass'),
        ('case str() as s if len(s) > 10:        return f"Long string: {s}"', 'MatchAs'),
        ('case "[]":        return "Empty list"', 'MatchValue'),
        ('case [first, *rest]:        return f"List with first element {first} and {len(rest)} more items"',
         'MatchSequence'),
        ('case {"name": name, "age": age}:        return f"Person named {name}, age {age}"', 'MatchMapping'),
        ('case Point(x=0, y=0):        return "Origin point"', 'MatchClass'),
        ('case Point(x=x, y=y):        return f"Point at ({x}, {y})"', 'MatchClass'),
        ('case "str":        return "Unknown data"', 'MatchValue'),
        ('case _:        return "Unknown data"', 'MatchAs'),
    ])
    def test_match_patterns(self, raw, kind):
        sample_code = f"match data:\n  {raw}\n  case _: pass"
        stmt = self.pattern_factory.create(sample_code)
        self.assertEqual(kind, stmt.children[1].children[0].children[0].kind)

    def test_match_stmt(self):
        sample_code = 'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        stmt = self.pattern_factory.create(sample_code)
        self.assertEqual('Match', stmt.kind)
        self.assertEqual('match_case', stmt.children[1].children[0].kind)
        self.assertEqual('MatchStar',
                         stmt.children[1].children[0].children[0].children[0].children[
                             1].kind)
        self.assertEqual('MatchAs', stmt.children[1].children()[1].children()[0].kind)

    @parameterized.expand([
        ('a % b', 'Mod'),
        ('a / b', 'Div'),
        ('a // b', 'FloorDiv'),
        ('a << b', 'LShift'),
        ('a >> b', 'RShift'),
        ('a * b', 'Mult'),
        ('a ** b', 'Pow'),
        ('a - b', 'Sub'),
        ('a + b', 'Add'),
    ])
    def test_binary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        self.assertEqual(kind, it.children()[1].kind)

    # @parameterized.expand([
    #     ('x = some_undefined_var', 'type_ignore'),
    #     ('-b', 'TypeVar'),
    #     ('~b', 'TypeVarTuple'),
    #     ('not b', 'ParamSpec'),
    # ])
    # def test_infer_types(self, raw, kind):
    #     it = self.factory.create_from_text(raw, 'context.py')
    #     kinds = [node.get_kind() for node in walk(it)]
    #     self.assertIn(kind, kinds)

    @parameterized.expand([
        ('+b', 'UAdd'),
        ('-b', 'USub'),
        ('~b', 'Invert'),
        ('not b', 'Not'),
    ])
    def test_unary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        self.assertEqual(kind, it.children()[0].kind)

    def test_show_call(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'apple.py')
        second_stmt = atu.children()[1]
        self.assertEqual(7, second_stmt.get_start_offset())
        self.assertEqual(7, second_stmt.get_length())
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
