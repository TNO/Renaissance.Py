import pytest
from parameterized import parameterized

from renaissance.impl import MATCH_ONE, MATCH_ALL
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import MatchFinder
from hamcrest import assert_that, is_equal

class TestPythonMatcher:


    def Setup(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    # @parameterized.expand([
    #     ('async for f in fs:  pass', 'AsyncFor'),
    #     ('try:\n  pass\nfinally:\n  pass', 'Try'),
    #     ('try:\n  x()\nexcept* e:\n  pass', 'TryStar'),
    #     ('class x:pass', 'ClassDef'),
    #     ('for i in items: pass', 'For'),
    #     ('while True: pass', 'While'),
    #     ('if True: pass', 'If'),
    #     ('async def fun(): pass', 'AsyncFunctionDef'),
    #     ('async with open("x"): pass', 'AsyncWith'),
    #     ('match x:\n  case _:    pass', 'Match'),
    #     ])
    def test_for_stmt(self):
        factory = ASTFactory(PythonASTNode, [])
        pattern_factory = PythonPatternFactory(self.factory)
        it = pattern_factory.create('for name in expr:\n  1\n  2\n  pass')
        assert_that(it.operator,is_equal("for"))
        assertEqual(it.name,"name")
        assertEqual(it.expr,"expr")
        assertEqual(len(it.body),3)

    #
    # def test_stmt_with_body(self):
    #     it = self.pattern_factory.create(raw)
    #     self.assertEqual(kind, it.kind)
    #     self.assertEqual(it.name,"name")
    #     self.assertEqual(it.type,"str")
    #     self.assertEqual(it.value,"value")
    @ parameterized.expand([
        ('i:int=0', 'AnnAssign'),
        ('x += 5', 'AugAssign'),
        ('assert 0', 'Assert'),
        ('break', 'Break'),
        ('continue', 'Continue'),
        ('fun()', 'Expr'),
        ('def fun(): pass', 'FunctionDef'),

        ('import x', 'Import'),

        ('from x import y', 'ImportFrom'),
        ('pass', 'Pass'),
        ('raise', 'Raise'),
        ('return', 'Return'),
    ])
    def test_stmt_kind(self, raw, kind):
        it = self.pattern_factory.create(raw)
        self.assertEqual(kind, it.kind)
        self.assertEqual(it.name,"name")
        self.assertEqual(it.type,"str")
        self.assertEqual(it.value,"value")

    def test_AnnAssign_node(self):
        it = self.pattern_factory.create('name:str = "value"')
        self.assertEqual(it.name,"name")
        self.assertEqual(it.type,"str")
        self.assertEqual(it.operator, "=")
        self.assertEqual(it.value,"value")

    def test_Assign_node(self):
        it = self.pattern_factory.create('name = "value"')
        self.assertEqual(it.name,"name")
        self.assertEqual(it.type,None)
        self.assertEqual(it.operator, "=")
        self.assertEqual(it.value,"value")

    def test_Assign_node(self):
        it = self.pattern_factory.create('name += 5', 'AugAssign')
        self.assertEqual(it.name, "name")
        self.assertEqual(it.type, None)
        self.assertEqual(it.operator, "+=")
        self.assertEqual(it.value, 5)

    def test_kind_is_match_one(self):
        simple = self.pattern_factory.create('$pa')
        self.assertEqual(MATCH_ONE, simple.kind)

    def test_kind_is_match_all(self):
        simple = self.pattern_factory.create('$$pa')
        self.assertEqual(MATCH_ALL, simple.kind)

    def test_match_one(self):
        simple = self.pattern_factory.create('$pa')
        self.assertEqual(self.atu.children[0], simple)

    def test_is_match_all_stmt(self):
        simple = self.pattern_factory.create('$$pa')
        self.assertTrue([simple] in self.atu)


    def test_is_match_all_stmt(self):
        simple = self.pattern_factory.create('$$pa')
        self.assertTrue( simple in self.atu)

    def test_is_exact_match(self):
        simple = self.pattern_factory.create('ba(55)')
        self.assertEqual(self.atu.children[0], simple)

    def test_match_exact_pattern(self):
        simple = self.pattern_factory.create('ba(55)')

        result = [ node for node in self.atu if node == simple]
        self.assertEqual(1, len(result))

    def test_match_single_pattern(self):
        simple = self.pattern_factory.create('$stmt')
        result = [ node for node in self.atu if node == simple]
        self.assertEqual(4, len(result))

    def test_match_single_call_pattern(self):
        simple = self.pattern_factory.create('$call($arg)')

        result = [ node for node in self.atu if node == simple]
        self.assertEqual(3, len(result))

    def test_match_pattern(self):
        simple = self.pattern_factory.create('$pa($55)')
        result = [ node for node in self.atu if node == simple]
        self.assertEqual(3, len(result))

    def test_find_all_using_generic_matcher(self):
        simple = self.pattern_factory.create('$pa(55)')

        self.assertEqual(self.atu[0], simple)
        self.assertNotEqual(self.atu[1], simple)
        self.assertNotEqual(self.atu[2], simple)
        self.assertNotEqual(self.atu[3], simple)

        result = [ node for node in self.atu if node == simple]
        self.assertEqual(1, len(result))

    def test_match_fun_using_generic_matcher(self):
        simple = self.pattern_factory.create('ca(555)')
        result = MatchFinder.find_all(self.atu.children, [simple]).to_list()
        self.assertTrue(simple in self.atu)

    def test_match_multiple(self):
        atu = self.factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55',
                                            'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')
        results = self.atu.find_all(simple)

        self.assertEqual(len(results[0].nodes), 3)
        self.assertEqual(len(results), 2)
