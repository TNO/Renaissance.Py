"""Tests for building Python AST patterns via PythonPatternFactory."""

import pytest
from hamcrest import assert_that, has_length, is_, is_in

from python.ast.factories import Factories
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.syntax_tree.pattern_kind import PatternKind


class TestPythonFactory:
    """AI: Tests for building Python AST patterns via PythonPatternFactory."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """AI: Build the shared Python factory and pattern factory used by the pattern-factory tests."""
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    # Statements patterns
    @pytest.mark.parametrize("statement", ["x = 10", "x += y", "name = 'John'", "a, b, c = (1, 2, 3)"])
    def test_statement(self, statement) -> None:
        """Test the creation of a statement in Python."""
        node = PythonRstNode.load_from_text(statement).body[-1]
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
        """AI: Verify if/elif/else statement variants parse with kind 'If' and preserve their signature."""
        node = PythonRstNode.load_from_text(statement).body[-1]
        assert_that(node.parser_kind, is_("If"))
        assert_that(node.signature, is_(statement))

    def test_import(self) -> None:
        """AI: Verify a from-import statement parses with kind 'ImportFrom' and exposes its module property."""
        statement = "from module import foo, bar"

        node = PythonRstNode.load_from_text(statement).body[-1]
        assert_that(node.parser_kind, is_("ImportFrom"))
        assert_that(node.signature, is_(statement))
        assert_that(node.properties["module"], is_("module"))

    @pytest.mark.parametrize(
        "statement",
        [
            "try:\n    pass\nexcept SomeException:\n    print('An error occurred.')",
            (
                "try:\n    pass\nexcept ExceptionType1:\n    print('An error occurred.')"
                "\nexcept ExceptionType2 as e:\n    print(f'Error: {e}')"
            ),
        ],
    )
    def test_try_statement(self, statement) -> None:
        """AI: Verify try/except statement patterns parse with kind 'Try' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(node.parser_kind, is_("Try"))
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
        """AI: Verify for-loop statement patterns parse with kind 'For' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(node.parser_kind, is_("For"))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "while True:\n    print(count)",
            "while count < 3:\n    print(count)\nelse:\n    print(count)",
        ],
    )
    def test_while_loop(self, statement) -> None:
        """AI: Verify while-loop statement patterns (with and without else) parse with kind 'While' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(node.parser_kind, is_("While"))
        assert_that(node.signature, is_(statement))

    @pytest.mark.parametrize(
        "statement",
        [
            "with MyContextManager('test') as cm:\n    print('Inside the context block')",
            "with open('example.txt', 'r') as file:\n    content = file.read()",
        ],
    )
    def test_with_statement(self, statement) -> None:
        """AI: Verify with-statement patterns parse with kind 'With' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(statement)
        assert_that(node.parser_kind, is_("With"))
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
        """AI: Verify function definition patterns parse with kind 'FunctionDef' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("FunctionDef"))
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
        """AI: Verify class definition patterns parse with kind 'ClassDef' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("ClassDef"))
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
        """AI: Verify return statement patterns parse with kind 'Return' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Return"))
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
        """Test for an assert statement.

        An assert statement has optionally a message.
        """
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Assert"))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize(
        "code",
        [
            "del x",
            "del my_set[0]",
        ],
    )
    def test_delete_statement(self, code) -> None:
        """AI: Verify delete statement patterns parse with kind 'Delete' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Delete"))
        assert_that(node.signature, is_(code))

    def test_pass(self) -> None:
        """AI: Verify a pass statement pattern parses with kind 'Pass' and preserves its signature."""
        code = "pass"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Pass"))
        assert_that(node.signature, is_(code))

    def test_break_statement(self) -> None:
        """AI: Verify a break statement pattern parses with kind 'Break' and preserves its signature."""
        code = "break"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Break"))
        assert_that(node.signature, is_(code))

    def test_cont_statement(self) -> None:
        """AI: Verify a continue statement pattern parses with kind 'Continue' and preserves its signature."""
        code = "continue"
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Continue"))
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
        """AI: Verify a bare variable name statement parses with kind 'Expr' and preserves its signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Expr"))
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
        """AI: Verify a variety of expression statements parse with kind 'Expr' and preserve their signature."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Expr"))
        assert_that(node.signature, is_(code))

    @pytest.mark.parametrize("code", ["\"hello = 'hello' # comment to hello\""])
    def test_comments(self, code) -> None:
        """Document that a `#` inside a string literal is not mistaken for a comment by the pattern factory."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_statement(code)
        assert_that(node.parser_kind, is_("Expr"))
        assert_that(node.signature, is_(code))

    def test_decorators(self) -> None:
        """AI: Verify creating a decorator pattern produces an ImplicitNode named 'decorator_list'."""
        pattern_factory = PythonPatternFactory(self.factory)
        node = pattern_factory.create_decorators("@parameterized.expand($exp)").node
        assert_that(node.parser_kind, is_("ImplicitNode"))
        assert_that(node.name, is_("decorator_list"))

    @pytest.mark.skip
    def test_match_decorators(self) -> None:
        """AI: Verify a decorator pattern matches an actual decorator on a parsed function (skipped test)."""
        node = self.factory.create_from_text(
            '@parameterized.expand("sasas")\ndef fun():\n    parameterized.expand("sasas")\n',
            "decorator_pattern.py",
        )
        pattern = self.pattern_factory.create_decorators("@parameterized.expand($exp)")
        result = match_pattern(node.children, [pattern])
        assert_that(result, has_length(1))

    def test_create_kwargs(self) -> None:
        """AI: Verify creating keyword-argument patterns matches the corresponding keywords of a real call."""
        pattern = self.pattern_factory.create_statement("fun($c=0, $d=2312)")
        kwargs = [PythonRstNode(kwarg) for kwarg in pattern.node.node.value.keywords]
        it = self.pattern_factory.create_kwargs("$c=0, $d=2312")
        assert_that(it[0], is_(kwargs[0]))

    @pytest.mark.parametrize(
        "_, factory, raw, expected",
        Factories.extend(
            [
                ("a = 1", ["Number", "Assign", "Literal", "Name", "AssignTarget", "Constant", "Integer", "assignment"]),
            ],
        ),
    )
    def test_misalignment(self, _, factory, raw, expected) -> None:
        """AI: Verify a numeric assignment expression's parser kind is one of several acceptable, backend-dependent kinds."""
        pattern_factory = PythonPatternFactory(factory)
        expression = pattern_factory.create_expression(raw)
        assert_that(expression.parser_kind, is_in(expected))

    def test_function_with_multi_patterns(self):
        """AI: Verify a call pattern mixing MATCH_ONE and MATCH_ALL placeholders assigns the expected pattern kinds to each child."""
        pattern = self.pattern_factory.create_expression("$f($$before, $a, $$after)")
        assert_that(pattern.parser_kind, is_("Call"))
        assert_that(pattern.children[0].pattern_kind, is_(PatternKind.MATCH_ONE))
        assert_that(pattern.children[1].children[0].pattern_kind, is_(PatternKind.MATCH_ALL))
        assert_that(pattern.children[1].children[1].pattern_kind, is_(PatternKind.MATCH_ONE))
        assert_that(pattern.children[1].children[2].pattern_kind, is_(PatternKind.MATCH_ALL))
