from itertools import product

import pytest
import ast

from hamcrest import assert_that, has_length, is_
from renaissance.impl.python import PythonASTNode
from renaissance.impl.python.python_cst_node import PythonCstNode
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.syntax_tree import ASTFactory
from renaissance.impl.python.python_pattern_factory import PythonPatternFactory
from renaissance.syntax_tree.match_finder import match_pattern


class Factories:
    # add factories here to test different ASTNode implementations
    node_types = [("ast", PythonASTNode),
                  ("cst", PythonCstNode),
                  ("lst", LSTNode),
                  ("rst", ast.AST), ]
    factories = [(name_type[0], ASTFactory(name_type[1])) for name_type in node_types]

    @staticmethod
    def extend(test_parameters: list[tuple]) -> list[tuple]:
        result = [
            (str(factory[0]) + " " + str(pars[0]), factory[1], *pars) for factory, pars in product(Factories.factories, test_parameters)
        ]
        return result

class TestPythonFactory:

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.factory = ASTFactory(PythonASTNode, [])
        self.pattern_factory = PythonPatternFactory(self.factory)

    # Statements patterns
    @pytest.mark.parametrize("statement", ["x = 10", "x += y", "name = 'John'", "a, b, c = (1, 2, 3)"])
    def test_statement(self, statement) -> None:
        """
        Test the creation of a statement in Python
        """
        node = PythonASTNode.load_from_text(statement).body[-1]
        assert_that(node.is_statement, is_(True))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "if a:\n    pass\nelif b:\n    pass\nelse:\n    pass",
            "if a:\n    pass\nelif b:\n    pass",
            "if a:\n    pass\nelse:\n    pass",
            "if a:\n    pass",
        ],
    )
    def test_if_else(self, statement) -> None:
        node = PythonASTNode.load_from_text(statement).body[-1]
        assert_that(ast.If.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    def test_import(self) -> None:
        statement = "from module import foo, bar"

        node = PythonASTNode.load_from_text(statement).body[-1]
        assert_that(ast.ImportFrom.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))
        assert_that(node.properties["module"], is_("module"))

    @pytest.mark.parametrize(
        "statement",
        [
            "try:\n    pass\nexcept SomeException:\n    print('An error occurred.')",
            "try:\n    pass\nexcept ExceptionType1:\n    print('An error occurred.')\nexcept ExceptionType2 as e:\n    print(f'Error: {e}')",
        ],
    )
    def test_try_statement(self, statement) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(ast.Try.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "for i in range(2, 11, 2):\n    print(i)",
            "for index, color in enumerate(colors):\n    print(f'Index {index}: {color}')",
            "for i in range(5):\n    print(i)",
        ],
    )
    def test_for_loop(self, statement) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(ast.For.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "while True:\n    print(count)",
            "while count < 3:\n    print(count)\nelse:\n    print(count)",
        ],
    )
    def test_while_loop(self, statement) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(ast.While.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "with MyContextManager('test') as cm:\n    print('Inside the context block')",
            "with open('example.txt', 'r') as file:\n    content = file.read()",
        ],
    )
    def test_with_statement(self, statement) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(ast.With.__name__, is_(node.kind))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "code",
        [
            "def greet():\n    print('Hello, World!')",
            "def multiply(x, y):\n    return x * y",
            "def outer_function(x):\n\n    def inner_function(y):\n        return y * 2\n    return inner_function(x) + 5",
        ],
    )
    def test_func_def(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.FunctionDef.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "class Person:\n\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age",
            "class MathHelper:\n    pi = 3.14159",
            "class Dog(Animal):\n\n    def speak(self):\n        return f'{self.name} says Woof!'",
        ],
    )
    def test_class_def(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.ClassDef.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "return a + b",
            "return (length, width, height)",
            "return 'Eligible to vote'",
        ],
    )
    def test_return_statement(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Return.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "assert length > 0, 'Length must be positive'",
            "assert 10 <= value <= 20, 'Value must be between 10 and 20'",
            "assert size < 12",
        ],
    )
    def test_assert_statement(self, code) -> None:
        """
        test for an assert statement.
        An assert statement has optionally a message.
        """
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Assert.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "del x",
            "del my_set[0]",
        ],
    )
    def test_delete_statement(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Delete.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_pass(self) -> None:
        code = "pass"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Pass.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_break_statement(self) -> None:
        code = "break"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Break.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_cont_statement(self) -> None:
        code = "continue"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Continue.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "del x",
            "del my_set[0]",
        ],
    )
    def test_variable_ref(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Delete.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    ### Expressions patterns
    @pytest.mark.parametrize(
        "code",
        [
            "a",
            "x",
        ],
    )
    def test_variable(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "Literal['left', 'center', 'right']",
            "('left', 'center', 'right')",
            "Final",
            "5 > 3",
            "str",
            "a + b",
            "not a",
            "a or b",
            "Person(name='Bob', age=25, job='Designer')",
            "a.attr",
            "a[b]",
            "a if b else c",
        ],
    )
    def test_expr(self, code) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", ["\"hello = 'hello' # comment to hello\""])
    def test_comments(self, code) -> None:
        """
        TODO: what is tested?
        """
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(ast.Expr.__name__, is_(node.kind))
        assert_that(node.signature, is_(code))

    def test_decorators(self) -> None:
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_decorators("@parameterized.expand($exp)").node
        assert_that(node.kind, is_("ImplicitNode"))
        assert_that(node.name, is_("decorator_list"))

    def test_match_decorators(self) -> None:
        node = self.factory.create_from_text(
            '@parameterized.expand("sasas")\ndef fun():\n    parameterized.expand("sasas")\n',
            "decorator_pattern.py",
        )
        pattern = self.pattern_factory.create_decorators("@parameterized.expand($exp)")
        result = match_pattern(node.children, [pattern])
        assert_that(result, has_length(1))

    def test_create_kwargs(self) -> None:
        pattern = self.pattern_factory.create_statement("fun($c=0, $d=2312)")
        kwargs = [PythonASTNode(kwarg) for kwarg in pattern.node.node.value.keywords]
        it = self.pattern_factory.create_kwargs("$c=0, $d=2312")
        assert_that(it[0], is_(kwargs[0]))

    @pytest.mark.parametrize(
        "_, factory, expression, expected",
        Factories.extend(
            [( "a = 1","(BINARY_OPERATOR"),]
        ),
    )
    @pytest.mark.skip("not working yet")
    def test(self, _, factory, expression, expected) -> None:
        patternFactory = PythonPatternFactory(factory)
        node = patternFactory.create_expression(expression)
        assert_that(node, is_(expected))
