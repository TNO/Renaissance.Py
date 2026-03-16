import pytest
import ast

from hamcrest import assert_that, has_length, is_
from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTFactory
from renaissance.impl.python.python_pattern_factory import PythonPatternFactory
from renaissance.syntax_tree.match_finder import match_pattern


class TestPythonFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])

    # Statements patterns
    @pytest.mark.parametrize("statement", [
        'x = 10',
        'x += y',
        'name = \'John\'',
        'a, b, c = (1, 2, 3)'
    ])
    def test_statement(self, statement):
        """
        Test the creation of a statement in Python
        """
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(True, node.is_statement)
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize("statement", [
        'if a:\n    pass\nelif:\n    pass\nelse:\n    pass',
        'if a:\n    pass\nelif:\n    pass',
        'if a:\n    pass\nelse:\n    pass',
        'if a:\n    pass\n',
    ])
    def test_if_else(self, statement):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(ast.If.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    def test_import(self):
        imp = 'from module import foo, bar'
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(imp)
        assert_that(ast.ImportFrom.__name__, is_(node.kind))
        assert_that(node.signature, is_(imp))

    @pytest.mark.parametrize("statement", [
        'try:\n    pass\nexcept SomeException:\n    print(\'An error occurred.\')',
        'try:\n    pass\nexcept ExceptionType1:\n    print(\'An error occurred.\')\nexcept ExceptionType2 as e:\n    print(f\'Error: {e}\')',
    ])
    def test_try_statement(self, statement):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(ast.Try.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize("statement", [
        'for i in range(2, 11, 2):\n    print(i)',
        'for index, color in enumerate(colors):\n    print(f\'Index {index}: {color}\')',
        'for i in range(5):\n    print(i)',
    ])
    def test_for_loop(self, statement):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(ast.For.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize("statement", [
        'while True:\n    print(count)',
        'while count < 3:\n    print(count)\nelse:\n    print(count)',
    ])
    def test_while_loop(self, statement):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(ast.While.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize("statement", [
        'with MyContextManager(\'test\') as cm:\n    print(\'Inside the context block\')',
        'with open(\'example.txt\', \'r\') as file:\n    content = file.read()',
    ])
    def test_with_statement(self, statement):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(statement)
        assert_that(ast.With.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize("code", [
        'def greet():\n    print(\'Hello, World!\')',
        'def multiply(x, y):\n    return x * y',
        'def outer_function(x):\n\n    def inner_function(y):\n        return y * 2\n    return inner_function(x) + 5',
    ])
    def test_func_def(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.FunctionDef.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'class Person:\n\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age',
        'class MathHelper:\n    pi = 3.14159',
        'class Dog(Animal):\n\n    def speak(self):\n        return f\'{self.name} says Woof!\'',
    ])
    def test_class_def(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.ClassDef.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'return a + b',
        'return (length, width, height)',
        'return \'Eligible to vote\'',
    ])
    def test_return_statement(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Return.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'assert length > 0, \'Length must be positive\'',
        'assert 10 <= value <= 20, \'Value must be between 10 and 20\'',
    ])
    def test_assert_statement(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Assert.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'del x',
        'del my_set[0]',
    ])
    def test_delete_statement(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Delete.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_pass(self):
        code = 'pass'
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Pass.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_break_statement(self):
        code = 'break'
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Break.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_cont_statement(self):
        code = 'continue'
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Continue.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'del x',
        'del my_set[0]',
    ])
    def test_variable_ref(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Delete.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    ### Expressions patterns
    @pytest.mark.parametrize("code", [
        'a',
        'x',
    ])
    def test_variable(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        'Literal[\'left\', \'center\', \'right\']',
        '(\'left\', \'center\', \'right\')',
        'Final',
        '5 > 3',
        'str',
        'a + b',
        'not a',
        'a or b',
        'Person(name=\'Bob\', age=25, job=\'Designer\')',
        'a.attr',
        'a[b]',
        'a if b else c',
    ])
    def test_expr(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", [
        '"hello = \'hello\' # comment to hello"'
    ])
    def test_comments(self, code):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_python_pattern(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_decorators(self):
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_decorators('@parameterized.expand($exp)')
        assert_that(node.kind,is_('ImplicitNode'))
        assert_that(node.name,is_('decorator_list'))


    def test_match_decorators(self):
        pattern_factory = PythonPatternFactory(self.factory)
        pattern = pattern_factory.create_decorators('@parameterized.expand($exp)')
        node = PythonASTNode.load_from_text('@parameterized.expand("sasas")\ndef fun():\n    parameterized.expand("sasas")\n')
        result = match_pattern(node.children,[pattern])
        assert_that(result, has_length(1))

