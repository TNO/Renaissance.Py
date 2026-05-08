from ast import AST

import pytest
from hamcrest import (
    assert_that,
    is_in,
    is_, instance_of,
)

from renaissance.impl.python.cst_node import PythonCstNode
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.tree_sitter.lst import LSTNode
from python.factories import Factories
from renaissance.impl.python.factory import PythonPatternFactory
from renaissance.impl.types import *
from renaissance.utils.ast_utils import traverse


class TestPythonNodes:

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("i:int=0", Assign),
                ("assert 0", Assert),
                ("async for f in fs:  pass", For),
                ("async def fun(): pass", FunctionDef),
                ('async with open("x"): pass', With),
                ("x += 5", AugAssign),
                ("break", Break),
                ("class x:pass", ClassDef),
                ("continue", Continue),
                ("fun()", ExpressionStatement),
                ("def fun(): pass", FunctionDef),
                ("for i in items: pass", For),
                ("import x", Import),
                ("if True: pass", If),
                ("from x import y", ImportFrom),
                ("match x:\n  case _:    pass", Match),
                ("pass", Pass),
                ("raise", Raise),
                ("return", Return),
                ("try:\n  pass\nfinally:\n  pass", Try),
                ("try:\n  x()\nexcept* e:\n  pass", Try),
                ("while True: pass", While),
            ],
        ),
    )
    def test_stmt_kind(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_statement(raw)
        assert_that(it.ast_type(), instance_of(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("with open() as c: pass", "With"),
                ("await (fun(2))", "Await"),
                ("a = 5 + 3", "BinaryOperation"),
                ("0x01 & 0x10", "BitAnd" ""),
                ("0x01 | 0x10", "BitOr"),
                ("0x01 ^ 0x10", "BitXor"),
                ("True and False", "BooleanOperation"),
                ("del x", "Delete"),
                (
                    """
def outer():
    x = 10
    y = 20
    def inner():
        nonlocal x, y
        x += 5
    return inner()
""",
                    "Nonlocal",
                ),
            ],
        ),
    )
    def test_stmt_kind_in_context(self, _, factory, raw, kind):
        it = factory.create_from_text(raw, "context.py")
        kinds = [node.ast_type for node in traverse(it) if hasattr(node, "ast_type")]
        assert_that(kind, is_in(kinds))

    @pytest.mark.parametrize("_, factory, raw, kind", Factories.extend([("global x", [Global, Statement])]))
    def test_global_stmt(self, _, factory, raw, kind):
        it = factory.create_from_text(raw).children[-1]
        assert_that(it.ast_type(), instance_of(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("fun()", "Call"),
                ("{one: 1, two:2}", "Dict"),
                ("{1,2}", "Set"),
                ("[1, 2]", "List"),
                ('{word: len(word) for word in ["one","two"]}', "DictComp"),
                ("[ n*3 for n in [1, 2]]", "ListComp"),
                ("{ n*3 for n in [1, 2]}", "SetComp"),
                ("lambda: fun()", "Lambda"),
                ("x = (n*2 for n in[1,2])", "GeneratorExp"),
                ('f"{one}two"', "FormattedString"),
                ("items[1:4]", "Subscript"),
                ("(9, 10)", "Tuple"),
                ("x = not True", "UnaryOperation"),
                ("yield fun", "Yield"),
                ("yield from [1,2]", "Yield"),
                ("x = z if z>y else y", "IfExp"),
            ],
        ),
    )
    def test_expr_kind(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        if type(it.node).__name__ != "LSTNode":
            assert_that(it.kind, is_(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("a == b", "Equal"),
                ("a in b", "In"),
                ("a is b", "Is"),
                ("a is not b", "IsNot"),
                ("a < b", "LessThan"),
                ("a <=b", "LessThanEqual"),
                ("a != b", "NotEqual"),
                ("a not in b", "NotIn"),
                ("a > b", "GreaterThan"),
                ("a >= b", "GreaterThanEqual"),
            ],
        ),
    )
    def test_comperator_operator(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        if isinstance(it.node, (AST, LSTNode)):
            assert_that(it.children[1].kind, is_(kind))
        else:
            assert_that(it.children[1].children[0].kind, is_(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ('case None: return "No data"', "MatchSingleton"),
                ('case True | False:        return "Boolean value"', "MatchOr"),
                (
                    'case int(x) if x > 0:        return f"Positive integer: {x}"',
                    "MatchClass",
                ),
                (
                    'case str() as s if len(s) > 10:        return f"Long string: {s}"',
                    "MatchAs",
                ),
                ('case "[]":        return "Empty list"', "MatchValue"),
                (
                    'case [first, *rest]:        return f"List with first element {first} and {len(rest)} more items"',
                    "MatchSequence",
                ),
                (
                    'case {"name": name, "age": age}:        return f"Person named {name}, age {age}"',
                    "MatchMapping",
                ),
                ('case Point(x=0, y=0):        return "Origin point"', "MatchClass"),
                (
                    'case Point(x=x, y=y):        return f"Point at ({x}, {y})"',
                    "MatchClass",
                ),
                ('case "str":        return "Unknown data"', "MatchValue"),
                ('case _:        return "Unknown data"', "MatchAs"),
            ],
        ),
    )
    def test_match_patterns(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        sample_code = f"match data:\n  {raw}\n  case _: pass"
        stmt = pattern_factory.create_statement(sample_code)
        if isinstance(stmt.node, PythonRstNode):
            case_kind = stmt.children[1].children[0].children[0].kind
        elif isinstance(stmt.node, AST):
            case_kind = stmt.children[1].children[0].kind
        elif isinstance(stmt.node, PythonCstNode):
            case_kind = stmt.children[4].children[1].kind
        elif isinstance(stmt.node, LSTNode):
            case_kind = stmt.children[3].children[0].children[1].kind
            return
        assert_that(case_kind, is_(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("a % b", Modulo),
                ("a / b", Divide),
                ("a // b", FloorDiv),
                ("a << b", LeftShift),
                ("a >> b", RightShift),
                ("a * b", Multiply),
                ("a ** b", Power),
                ("a - b", Subtract),
                ("a + b", Add),
            ],
        ),
    )
    def test_binary_operator(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        assert_that(it.children[1].ast_type(), instance_of(kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("+b", UnaryAdd),
                ("-b", UnarySubtract),
                ("~b", Invert),
                ("not b", NotOperator),
            ],
        ),
    )
    def test_unary_operator(self, _, factory, raw, kind):
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        assert_that(it.ast_type(), instance_of(UnaryOperation))
        if not isinstance(it.node, LSTNode):
            assert_that(it.children[0].ast_type(), instance_of(kind))
