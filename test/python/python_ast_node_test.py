import ast

import ast
from ast import unparse

import pytest
from pathlib import Path

from hamcrest import has_length, assert_that, is_in, is_, contains_string
from parameterized import parameterized

import targets
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.syntax_tree.match_finder import is_match
from renaissance.utils.node_util import traverse
from utils_for_tests import show_node


class TestPythonASTNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('a = 0', 'all.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    @pytest.mark.parametrize("raw, kind", [
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
        assert kind == it.kind

    @pytest.mark.parametrize("raw, kind", [
        ('with open() as c: pass', 'With'),
        ('await (fun(2))', 'Await'),
        ('a = 5 + 3', 'BinOp'),

        ('0x01 & 0x10', 'BitAnd'''),
        ('0x01 | 0x10', 'BitOr'),
        ('0x01 ^ 0x10', 'BitXor'),
        ('True and False', 'BoolOp'),
        ('global x', 'Global'),
        ('del x', 'Delete'),
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
        kinds = [node.kind for node in traverse(it)]
        assert_that(kind, is_in(kinds))


    @pytest.mark.skip("it was working before")
    def test_TypeAlias(self):
        it = self.factory.create_from_text('type UserId = int', 'context.py')
        show_node(it)
        kinds = [node.kind for node in traverse(it)]
        assert_that('TypeAlias', is_in(kinds))
        

    @pytest.mark.parametrize("raw, kind", [
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
        assert_that(kind, is_(it.kind))

    def test_Slice(self):
        it = self.pattern_factory.create_expression('items[1:2:3]')
        assert_that('Slice', is_(it.children[1].kind))

    def test_NamedExpr(self):
        it = self.pattern_factory.create('if n:= len(items): pass')
        assert_that('NamedExpr', is_(it.children[0].kind))

    def test_Starred(self):
        it = self.pattern_factory.create('*x =[1,2]')
        assert_that('Starred', is_(it.children[0].children[0].kind))

    def test_FormattedValue(self):
        it = self.pattern_factory.create_expression('f"{one}two"')
        assert_that('FormattedValue', is_(it.children[0].kind))

    def test_ExceptHandler(self):
        it = self.pattern_factory.create('try: pass\nexcept NameError:pass')
        assert_that('ExceptHandler', is_(it.children[1].children[0].kind))

    @pytest.mark.parametrize("raw, kind", [
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
        assert_that(kind, is_(it.children[1].children[0].kind))

    @pytest.mark.parametrize("raw, kind", [
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
        assert_that(kind, is_(stmt.children[1].children[0].children[0].kind))

    def test_match_stmt(self):
        sample_code = 'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        stmt = self.pattern_factory.create(sample_code)
        assert_that('Match', is_(stmt.kind))
        assert_that('match_case', is_(stmt.children[1].children[0].kind))
        assert_that('MatchStar', is_(stmt.children[1].children[0].children[0].children[1].kind))
        assert_that('MatchAs', is_(  stmt.children[1].children[0].children[0].children[0].kind))

    @pytest.mark.parametrize("raw, kind", [
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
        assert_that(kind, is_(it.children[1].kind))

    # @parameterized.expand([
    #     ('x = some_undefined_var', 'type_ignore'),
    #     ('-b', 'TypeVar'),
    #     ('~b', 'TypeVarTuple'),
    #     ('not b', 'ParamSpec'),
    # ])
    # def test_infer_types(self, raw, kind):
    #     it = self.factory.create_from_text(raw, 'context.py')
    #     kinds = [node.kind for node in walk(it)]
    #     assert_that(kind, is_in(kinds))

    @pytest.mark.parametrize("raw, kind", [
        ('+b', 'UAdd'),
        ('-b', 'USub'),
        ('~b', 'Invert'),
        ('not b', 'Not'),
    ])
    def test_unary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(kind, is_(it.children[0].kind))

    def test_show_call(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'apple.py')
        second_stmt = atu.children[1]
        assert_that(7, is_(second_stmt.offset))
        assert_that(7, is_(second_stmt.length))
        assert_that('apple.py', is_(second_stmt.filename))
        assert_that(atu.translation_unit, is_(second_stmt.translation_unit))

    def test_show_call_with_args(self):
        src = self.pattern_factory.create_statement('def ba(a55,a66,a77,a88,a99): pass')
        cmp = self.pattern_factory.create_statement('def ba($$args): pass')
        expansions={}
        assert is_match(src,cmp, expansions)
        assert '$$args' in expansions
        assert  len(expansions['$$args']) == 5

    def test_attribute_signature_has_at(self):
        src = self.pattern_factory.create_statement('@TUAT\ndef ba(): pass')
        ASTShower.show_node(src)
        attr = src.children[2].children[0]
        assert attr.signature == '@TUAT'

    def test_node_family(self):
        src = PythonASTNode.load_from_text('''
import you 
from other import dog
class Parent:
    def previous_me():
        pass
    def mememe(a55,a66,a77,a88,a99):
        l(a55)
        l(a66)
        l(a77)
        l(a88)
    def next_me():
        pass
    ''', 'nav.py',[], Path('.'))
        #          module  class     body        fun memem
        me = src.children[-1].children[2].children[1]
        assert_that(me.name, is_('mememe'))
        assert_that(me.preceding_sibling.name, is_('previous_me'))
        assert_that(me.next_sibling.name, is_('next_me'))
        assert_that(me.parent.parent.name, is_('Parent'))
        assert_that(me.children[1].children, has_length(4))

def test_load_file_with_ignored_types():
    atu = PythonASTNode.load_from_text('x = 1 # type: ignore', 'bogus.py',{}, Path(targets.__file__))
    assert_that(atu.translation_unit.atu.type_ignores, has_length(1))

def test_load_file():
    atu = PythonASTNode.load('demo.py',{}, Path(targets.__file__).parent)
    assert atu.translation_unit.atu.type_ignores ==[]

def test_load_invalid_file():
    with pytest.raises(IndentationError, match='unexpected indent'):
        PythonASTNode.load('invalid.py', {}, Path(targets.__file__).parent)

def test_annFun_to_str():
    annFun = '''
@parameterized.expand(Factories.extend(['$x;$y;']))
def test(_):
    atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")

    matches = match_pattern( func_body.children,patterns)

    self.assert_matches( expected_dicts_per_match,matches)
    '''
    it = PythonASTNode.load_from_text(annFun, 'fun.py',[], None).body[-1]
    assert_that(it.offset, is_(1))
    assert_that(it.signature , contains_string('@parameterized.expand'))

def test_annFun_to_str():
    annFun = '''
@parameterized.expand(Factories.extend(['$x;$y;']))
def test(_):
    atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")

    matches = match_pattern( func_body.children,patterns)

    self.assert_matches( expected_dicts_per_match,matches)
    '''
    it = PythonASTNode.load_from_text(annFun, 'fun.py',[], None).body[-1]
    assert str(it) == ast.unparse(it.node)
