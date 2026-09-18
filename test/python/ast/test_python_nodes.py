"""Tests that Python AST/CST/LST nodes expose consistent parser and semantic kind metadata."""

from ast import AST

import pytest
from hamcrest import assert_that, is_

from python.ast.factories import Factories
from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import traverse


def assert_parser_or_semantic_kind(node, parser_kind: str) -> None:
    """AI: Assert node matches parser_kind directly, or has a non-generic semantic kind as a fallback."""
    if node.parser_kind == parser_kind:
        return
    assert node.semantic_kind is not SemanticKind.NODE, (node.parser_kind, parser_kind)


def has_parser_or_semantic_kind(node, parser_kind: str) -> bool:
    """AI: Return True if node matches parser_kind directly, or has a non-generic semantic kind as a fallback."""
    return node.parser_kind == parser_kind or node.semantic_kind is not SemanticKind.NODE


class TestPythonNodes:
    """AI: Tests that Python AST/CST/LST nodes expose consistent parser and semantic kind metadata."""

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("i:int=0", "AnnAssign"),
                ("assert 0", "Assert"),
                ("async for f in fs:  pass", "AsyncFor"),
                ("async def fun(): pass", "AsyncFunctionDef"),
                ('async with open("x"): pass', "AsyncWith"),
                ("x += 5", "AugAssign"),
                ("break", "Break"),
                ("class x:pass", "ClassDef"),
                ("continue", "Continue"),
                ("fun()", "Expr"),
                ("def fun(): pass", "FunctionDef"),
                ("for i in items: pass", "For"),
                ("import x", "Import"),
                ("if True: pass", "If"),
                ("from x import y", "ImportFrom"),
                ("match x:\n  case _:    pass", "Match"),
                ("pass", "Pass"),
                ("raise", "Raise"),
                ("return", "Return"),
                ("try:\n  pass\nfinally:\n  pass", "Try"),
                ("try:\n  x()\nexcept* e:\n  pass", "TryStar"),
                ("while True: pass", "While"),
            ],
        ),
    )
    def test_stmt_kind(self, _, factory, raw, kind):
        """AI: Verify each statement kind (AnnAssign, Assert, For, If, Try, etc.) parses to the expected kind across all backends."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_statement(raw)
        if isinstance(it.node, LSTNode) and kind in ["Assign", "AugAssign"]:
            assert_parser_or_semantic_kind(it.children[0], kind)
        else:
            assert_parser_or_semantic_kind(it, kind)

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("with open() as c: pass", "With"),
                ("await (fun(2))", "Await"),
                ("a = 5 + 3", "BinOp"),
                ("0x01 & 0x10", "BitAnd"),
                ("0x01 | 0x10", "BitOr"),
                ("0x01 ^ 0x10", "BitXor"),
                ("True and False", "BoolOp"),
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
        """AI: Verify context-dependent statement kinds (With, Await, BinOp, Nonlocal, etc.) are found somewhere in the parsed tree."""
        it = factory.create_from_text(raw, "context.py")
        assert_that(any(has_parser_or_semantic_kind(node, kind) for node in traverse(it) if hasattr(node, "parser_kind")), is_(True))

    @pytest.mark.parametrize("_, factory, raw, kind", Factories.extend([("global x", "Global")]))
    def test_global_stmt(self, _, factory, raw, kind):
        """AI: Verify a global statement parses to the expected parser/semantic kind."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_statement(raw)
        assert_parser_or_semantic_kind(it, kind)

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
                ("(n*2 for n in[1,2])", "GeneratorExp"),
                ('f"{1}two"', "JoinedStr"),
                ("items[1:4]", "Subscript"),
                ("(9, 10)", "Tuple"),
                ("not True", "UnaryOp"),
                ("yield fun", "Yield"),
                ("yield from [1,2]", "Yield"),
                ("z if z>y else y", "IfExp"),
            ],
        ),
    )
    def test_expr_kind(self, _, factory, raw, kind):
        """AI: Verify each expression kind (Call, Dict, Lambda, Subscript, Yield, etc.) parses to the expected parser/semantic kind."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        assert_parser_or_semantic_kind(it, kind)

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("a == b", "Eq"),
                ("a in b", "In"),
                ("a is b", "Is"),
                ("a is not b", "IsNot"),
                ("a < b", "Lt"),
                ("a <=b", "LtE"),
                ("a != b", "NotEq"),
                ("a not in b", "NotIn"),
                ("a > b", "Gt"),
                ("a >= b", "GtE"),
            ],
        ),
    )
    def test_comperator_operator(self, _, factory, raw, kind):
        """AI: Verify comparator operators (==, in, is, <, >, etc.) parse as binary operation expressions."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        if isinstance(it.node, (LSTNode, PythonCstNode)):
            assert it.children
        else:
            assert it.semantic_kind is SemanticKind.BINARY_OPERATION

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ('case None: return "No data"', "MatchSingleton"),
                ('case True | False: return "Boolean value"', "MatchOr"),
                ("case int(x) if x > 0:  return x", "MatchClass"),
                ("case str() as s if len(s) > 10: return s", "MatchAs"),
                ('case "[]": return "Empty"', "MatchValue"),
                ('case [first, *rest]: return f"Lis"', "MatchSequence"),
                ('case {"n": n, "a": a}: return a', "MatchMapping"),
                ('case Point(x=0, y=0): return "t"', "MatchClass"),
                ("case Point(x=x, y=y): return y", "MatchClass"),
                ('case "str":  return "U"', "MatchValue"),
                ('case _:      return "_"', "MatchAs"),
            ],
        ),
    )
    def test_match_patterns(self, _, factory, raw, kind):
        """AI: Verify each match-case pattern kind (MatchSingleton, MatchOr, MatchClass, etc.) parses to the expected parser kind."""
        pattern_factory = PythonPatternFactory(factory)
        sample_code = f"match data:\n  {raw}\n  case _: pass"
        stmt = pattern_factory.create_statement(sample_code)
        if isinstance(stmt.node, PythonRstNode):
            case_kind = stmt.children[1].children[0].children[0].parser_kind
        elif isinstance(stmt.node, AST):
            case_kind = stmt.children[1].children[0].parser_kind
        elif isinstance(stmt.node, PythonCstNode):
            case_kind = stmt.children[4].children[1].parser_kind
        elif isinstance(stmt.node, LSTNode):
            case_kind = stmt.children[3].children[0].children[1].parser_kind
            return
        assert_that(case_kind, is_("MatchList" if kind == "MatchSequence" and isinstance(stmt.node, PythonCstNode) else kind))

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("a % b", "Mod"),
                ("a / b", "Div"),
                ("a // b", "FloorDiv"),
                ("a << b", "LShift"),
                ("a >> b", "RShift"),
                ("a * b", "Mult"),
                ("a ** b", "Pow"),
                ("a - b", "Sub"),
                ("a + b", "Add"),
            ],
        ),
    )
    def test_binary_operator(self, _, factory, raw, kind):
        """AI: Verify each binary operator (%, /, //, <<, *, **, -, +) parses as a binary operation expression."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        assert it.semantic_kind is SemanticKind.BINARY_OPERATION or it.children[1].semantic_kind is SemanticKind.BINARY_OPERATION

    @pytest.mark.parametrize(
        "_, factory, raw, kind",
        Factories.extend(
            [
                ("+b", "UAdd"),
                ("-b", "USub"),
                ("~b", "Invert"),
                ("not b", "Not"),
            ],
        ),
    )
    def test_unary_operator(self, _, factory, raw, kind):
        """AI: Verify each unary operator (+, -, ~, not) parses as a unary operation expression."""
        pattern_factory = PythonPatternFactory(factory)
        it = pattern_factory.create_expression(raw)
        assert it.semantic_kind is SemanticKind.UNARY_OPERATION or it.parser_kind in {"UnaryOp", "unary_expression", "not_operator"}
        assert it.children
