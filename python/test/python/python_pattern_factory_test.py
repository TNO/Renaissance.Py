import unittest
import ast
from .factories import Factories
from parameterized import parameterized
from impl.python.python_pattern_factory import PythonPatternFactory

class PythonFactoryTestCase(unittest.TestCase):

    # Statements patterns
    @parameterized.expand(Factories.extend([
        ('x = 10', ...),
        ('x += y', ...),
        ('name = \'John\'', ...),
        ('a, b, c = (1, 2, 3)', ...)
    ]))
    def test_statement(self, _, factory, statement, *args):
        """
        Test the creation of a statement in Python
        """
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertTrue(node.is_statement)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.factories)
    def test_import(self, _, factory):
        imp = 'from module import foo, bar'
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(imp)
        self.assertEqual(node.kind, ast.ImportFrom.__name__)
        self.assertEqual(imp, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('if a:\n    pass\nelse:\n    pass', ...),
        ('if a:\n    pass\nelse:\n    pass', ...),
    ]))
    def test_if_else(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertEqual(node.kind, ast.If.__name__)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('try:\n    pass\nexcept SomeException:\n    print(\'An error occurred.\')', ...),
        ('try:\n    pass\nexcept ExceptionType1:\n    print(\'An error occurred.\')\nexcept ExceptionType2 as e:\n    print(f\'Error: {e}\')', ...),
    ]))
    def test_try_statement(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertEqual(node.kind, ast.Try.__name__)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('for i in range(2, 11, 2):\n    print(i)', ...),
        ('for index, color in enumerate(colors):\n    print(f\'Index {index}: {color}\')', ...),
        ('for i in range(5):\n    print(i)', ...)
    ]))
    def test_for_loop(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertEqual(node.kind, ast.For.__name__)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('while True:\n    print(count)', ...),
        ('while count < 3:\n    print(count)\nelse:\n    print(count)', ...),
    ]))
    def test_while_loop(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertEqual(node.kind, ast.While.__name__)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('with MyContextManager(\'test\') as cm:\n    print(\'Inside the context block\')', ...),
        ('with open(\'example.txt\', \'r\') as file:\n    content = file.read()', ...),
    ]))
    def test_with_statement(self, _, factory, statement, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(statement)
        self.assertEqual(node.kind, ast.With.__name__)
        self.assertEqual(statement, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('def greet():\n    print(\'Hello, World!\')', ...),
        ('def multiply(x, y):\n    return x * y', ...),
        ('def outer_function(x):\n\n    def inner_function(y):\n        return y * 2\n    return inner_function(x) + 5', ...),
    ]))
    def test_func_def(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.FunctionDef.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('class Person:\n\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age', ...),
        ('class MathHelper:\n    pi = 3.14159', ...),
        ('class Dog(Animal):\n\n    def speak(self):\n        return f\'{self.name} says Woof!\'',
         ...),
    ]))
    def test_class_def(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.ClassDef.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('return a + b', ...),
        ('return (length, width, height)', ...),
        ('return \'Eligible to vote\'', ...),
    ]))
    def test_return_statement(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Return.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('assert length > 0, \'Length must be positive\'', ...),
        ('assert 10 <= value <= 20, \'Value must be between 10 and 20\'', ...),
    ]))
    def test_assert_statement(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Assert.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('del x', ...),
        ('del my_set[0]', ...),
    ]))
    def test_delete_statement(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Delete.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.factories)
    def test_pass(self, _, factory):
        code = 'pass'
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Pass.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.factories)
    def test_break_statement(self, _, factory):
        code = 'break'
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Break.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.factories)
    def test_cont_statement(self, _, factory):
        code = 'continue'
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Continue.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('del x', ...),
        ('del my_set[0]', ...),
    ]))
    def test_variable_ref(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Delete.__name__)
        self.assertEqual(code, node.raw_signature)

    ### Expressions patterns
    @parameterized.expand(Factories.extend([
        ('a', ...),
        ('x', ...),
    ]))
    def test_variable(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Expr.__name__)
        self.assertEqual(code, node.raw_signature)

    @parameterized.expand(Factories.extend([
        ('Literal[\'left\', \'center\', \'right\']', ...),
        ('(\'left\', \'center\', \'right\')', ...),
        ('Final', ...),
        ('5 > 3', ...),
        ('str', ...),
        ('a + b', ...),
        ('not a', ...),
        ('a or b', ...),
        ('Person(name=\'Bob\', age=25, job=\'Designer\')', ...),
        ('a.attr', ...),
        ('a[b]', ...),
        ('a if b else c', ...),
    ]))
    def test_expr(self, _, factory, code, *args):
        pattern_factory = PythonPatternFactory(factory)
        node = pattern_factory.create_python_pattern(code)
        self.assertEqual(node.kind, ast.Expr.__name__)
        self.assertEqual(code, node.raw_signature)


if __name__ == '__main__':
    unittest.main()
