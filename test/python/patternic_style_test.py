from operator import is_not

import pytest
from parameterized import parameterized

from renaissance.impl import MATCH_ONE, MATCH_ALL
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import MatchFinder
from hamcrest import assert_that, is_, has_length, is_in,is_not
import hamcrest
class TestPythonicStyle:
    @parameterized.expand([
    #     ('async for f in fs:  pass', 'AsyncFor'),
        ('try:\n  pass\nfinally:\n  pass', 'Try', 'try','Try',1),
        ('class name: pass', 'ClassDef', 'class', 'name',  1),
    #     ('async def fun(): pass', 'AsyncFunctionDef'),
        ('def name(): pass', 'FunctionDef', 'function','name',1),
    ])
    def test_consistent_decl(self, raw, kind, op, name, body_length):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        it = pattern_factory.create(raw)
        assert_that(it.kind, is_(kind))
        assert_that(it.operator, is_(op))
        assert_that(it.name,is_(name))
        assert_that(it.expr,is_(None))
        assert_that(it.body, has_length(body_length))

    @parameterized.expand([
        #     ('try:\n  x()\nexcept* e:\n  pass', 'TryStar'),
       ('for name in expr:\n  1\n  2\n  pass', 'For', 'for','name','expr',3),
        ('while expr: pass', 'While', 'while','While','expr',1),
        ('if expr: pass\nelse: pass ', 'If', 'if','If','expr',1),
    #     ('async with open("x"): pass', 'AsyncWith'),
    #     ('match x:\n  case _:    pass', 'Match'),
        ])
    def test_consistent_name_stmt(self, raw, kind, op, name, expr, body_length):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        it = pattern_factory.create(raw)
        assert_that(it.kind, is_(kind))
        assert_that(it.operator, is_(op))
        assert_that(it.name,is_(name))
        assert_that(it.expr.name,is_(expr))
        assert_that(it.body, has_length(body_length))

    #
    # def test_stmt_with_body(self):
    #     it = self.pattern_factory.create(raw)
    #     assert_that(kind, is_(it.kind))
    #     assert_that(it.name, is_("name"))
    #     assert_that(it.type, is_("str"))
    #     assert_that(it.value, is_("value"))
    @ parameterized.expand([
        ('i:int=0', 'AnnAssign','int','i','=',0),
        ('x += 5', 'AugAssign',None, 'x', "+=", 5),
        # ('assert 0', 'Assert',None, None, 'assert', 0),
        # ('break', 'Break',None, None, 'break', None),
        # ('continue', 'Continue', None, None, 'continue', None),
        # ('fun()', 'Expr', None, None, None, None, ),
        #
        # ('import x', 'Import',None, 'x', 'import', None),
        #
        # ('from x import y', 'ImportFrom',None, 'x', 'import', 'y'),
        # ('pass', 'Pass',None, None, 'pass', None,),
        # ('raise', 'Raise',None, None, 'raise', None,),
        # ('return', 'Return',None, None, 'return', None,),
    ])
    def test_stmt_kind(self, raw, kind,typ,name,op,value):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        it = pattern_factory.create(raw)
        assert_that(kind, is_(it.kind))
        assert_that(it.name, is_(name))
        assert_that(it.operator, op)
        assert_that(it.type, is_(typ))
        assert_that(it.value, is_(value))

    def test_AnnAssign_node(self):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        it = pattern_factory.create('name:str = "value"')

        assert_that(it.name, is_("name"))
        assert_that(it.type, is_("str"))
        assert_that(it.operator, is_("="))
        assert_that(it.value, is_("value"))

    def test_Assign_node(self):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        it = pattern_factory.create('name = "value"')

        assert_that(it.name, is_("name"))
        assert_that(it.type, is_(None))
        assert_that(it.operator, is_("="))
        assert_that(it.value, is_("value"))

    def test_Assign_node(self):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        it = pattern_factory.create('name += 5', 'AugAssign')
        assert_that(it.name, is_("name"))
        assert_that(it.type, is_(None))
        assert_that(it.operator, is_("+="))
        assert_that(it.value, is_(5))

    def test_kind_is_match_one(self):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        simple = pattern_factory.create('$pa')
        assert_that(MATCH_ONE, is_(simple.kind))

    def test_kind_is_match_all(self):
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        simple = pattern_factory.create('$$pa')
        assert_that(MATCH_ALL, is_(simple.kind))

    def test_match_one(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory)
        match_one = pattern_factory.create('$pa')
        assert_that(atu.children[0], is_(match_one))

    def test_is_match_all_stmt(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        match_all = pattern_factory.create('$$pa')
        assert_that(match_all, is_in(atu))

    def test_is_exact_match(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        stmt = pattern_factory.create('ba(55)')

        assert_that(atu.children[0], is_(stmt))

    def test_match_exact_pattern(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        stmt = pattern_factory.create('ba(55)')

        result = [ node for node in atu if node == stmt]

        assert_that(result, has_length(1))

    def test_match_single_pattern(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))
        match_any = pattern_factory.create('$stmt')

        result = [ node for node in atu if node == match_any]

        assert_that(result, has_length(4))

    def test_match_single_call_pattern(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        match_call = pattern_factory.create('$call($arg)')

        result = [ node for node in atu if node == match_call]

        assert_that(result, has_length(3))

    def test_find_all_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        simple = pattern_factory.create('$pa(55)')

        assert_that(atu[0], is_(simple))
        assert_that(atu[1], is_not(simple))
        assert_that(atu[2], is_not(simple))
        assert_that(atu[3], is_not(simple))

        result = [ node for node in atu if node == simple]
        assert_that(result, has_length(1))


    def test_match_fun_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        simple = pattern_factory.create('ca(555)')
        result = atu.find_all([simple])
        assert_that(result, has_length(1))

    def test_match_multiple(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(ASTFactory(PythonASTNode))

        stmt_list = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')
        results = atu.find_all(stmt_list)

        assert_that(results, has_length(2))
        assert_that(results[0].nodes, has_length(3))

    def test_slice_call(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55', 'test.py')
        slice = atu[0:3]
        assert_that(slice , has_length(3))


    def test_property_kind_call(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55', 'test.py')
        slice = atu.kind
        assert_that(slice , is_('Module'))

    def test_property_name_call(self):
        factory = ASTFactory(PythonASTNode)
        atu = factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55', 'test.py')
        slice = atu.name
        assert_that(slice , is_('Module'))
