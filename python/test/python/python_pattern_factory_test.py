import unittest
import ast
from impl import PythonASTNode
from .factories import Factories
from parameterized import parameterized
from impl.python.python_pattern_factory import PythonPatternFactory

class PythonFactoryTestCase(unittest.TestCase):

    @parameterized.expand(Factories.extend([
        ('x = 10', ...),
        ('x += y', ...),
        ('name = \'John\'', ...),
        ('a, b, c = 1, 2, 3', ...)
    ]))
    def test_statement(self, _, factory, statement, *args):
        """
        Test the creation of a statement in Python
        """
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_statement(statement)
        self.assertTrue(node.is_statement())
        #print(node.get_text())
        self.assertEqual(statement, node.get_text())

    @parameterized.expand(Factories.extend([
        ('5 > 3', ...),
        #('list(map(lambda x: x**2, [1, 2, 3, 4]))', ...),
        #('long_expression = component_one + component_two + component_three + component_four + component_five', ...),
    ]))
    def test_compareExpr(self, _, factory, expr, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_compare(expr)
        self.assertEqual(expr, node.get_text())

    @parameterized.expand(Factories.factories)
    def test_import(self, _, factory):
        imp = 'from module import foo, bar'
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_import(imp)
        self.assertEqual(node.get_kind(), ast.ImportFrom.__name__)
        self.assertEqual(imp, node.get_raw_signature())

    @parameterized.expand(Factories.extend([
        ('if a:\n    pass\nelse:\n    pass', ...),
        ('if a:\n    pass\nelse:\n    pass', ...),
    ]))
    def test_if_else(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_if_statement(statement)
        self.assertEqual(node.get_kind(), ast.If.__name__)
        self.assertEqual(statement, node.get_text())

    @parameterized.expand(Factories.extend([
        ('try:\n    pass\nexcept SomeException:\n    print(\'An error occurred.\')', ...),
        ('try:\n    pass\nexcept ExceptionType1:\n    print(\'An error occurred.\')\nexcept ExceptionType2 as e:\n    print(f\'Error: {e}\')', ...),
    ]))
    def test_try_statement(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_try_statement(statement)
        self.assertEqual(node.get_kind(), ast.Try.__name__)
        self.assertEqual(statement, node.get_text())

if __name__ == '__main__':
    unittest.main()
