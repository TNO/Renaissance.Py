import ast
import textwrap
from pathlib import Path

import pytest
from hamcrest import (
    has_length,
    assert_that,
    is_in,
    is_,
    contains_string,
    empty,
    is_not,
)
from libcst import ParserSyntaxError

import targets

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.cst_node import PythonCstNode
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.utils.ast_utils import traverse


class TestPythonCstNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonCstNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("i:int=0", "AnnAssign"),
            ("assert 0", "Assert"),
            ("x += 5", "AugAssign"),
            ("break", "Break"),
            ("continue", "Continue"),
            ("fun()", "Expr"),
            ("import x", "Import"),
            ("from x import y", "ImportFrom"),
            ("pass", "Pass"),
            ("raise", "Raise"),
            ("return", "Return"),
        ],
    )
    def test_stmt_kind(self, raw, kind):
        it = self.pattern_factory.create_statement(raw)
        assert_that(it.kind, is_(kind))
        assert_that(it.node.is_statement, is_(True))

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("async for f in fs:  pass", "For"),
            ("async def fun(): pass", "FunctionDef"),
            ('async with open("x"): pass', "With"),
            ("class x:pass", "ClassDef"),
            ("def fun(): pass", "FunctionDef"),
            ("for i in items: pass", "For"),
            ("if True: pass", "If"),
            ("match x:\n  case _:    pass", "Match"),
            ("try:\n  pass\nfinally:\n  pass", "Try"),
            ("try:\n  x()\nexcept* e:\n  pass", "TryStar"),
            ("while True: pass", "While"),
        ],
    )
    def test_stmt_kind2(self, raw, kind):
        it = self.pattern_factory.create_statement(raw)
        assert_that(it.kind, is_(kind))
        assert_that(it.node.is_statement, is_(True))

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("with open() as c: pass", "With"),
            ("await (fun(2))", "Await"),
            ("a = 5 + 3", "BinaryOperation"),
            ("0x01 & 0x10", "BitAnd" ""),
            ("0x01 | 0x10", "BitOr"),
            ("0x01 ^ 0x10", "BitXor"),
            ("True and False", "BooleanOperation"),
            ("del x", "Del"),
            (
                "def outer():\n    x = 10\n    y = 20\n    def inner():\n        nonlocal x, y\n        x += 5\n    return inner()",
                "Nonlocal",
            ),
        ],
    )
    def test_stmt_kind_in_context(self, raw, kind):
        it = self.factory.create_from_text(raw, "context.py")
        kinds = [node.kind for node in traverse(it)]
        assert_that(kind, is_in(kinds))

    def test_global_stmt(self):
        it = self.factory.create_from_text("global x", "context.py").children[-1]
        assert_that(it.kind, is_("SimpleStatementLine"))
        assert_that(it.children[0].kind, is_("Global"))

    @pytest.mark.parametrize(
        "raw, kind",
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
            ('f"{one}two"', "FormattedString"),
            ("items[1:4]", "Subscript"),
            ("(9, 10)", "Tuple"),
            ("not True", "UnaryOperation"),
            ("yield fun", "Yield"),
            ("yield from [1,2]", "Yield"),
            ("z if z>y else y", "IfExp"),
        ],
    )
    def test_expr_kind(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(it.kind, is_(kind))

    def test_type_alias(self):
        it = self.factory.create_from_text("type UserId = int", "context.py")
        kinds = [node.kind for node in traverse(it)]
        assert_that("TypeAlias", is_in(kinds))

    def test_slice(self):
        it = self.pattern_factory.create_expression("items[1:2:3]")
        assert_that(it.children[0].kind, is_("Name"))
        assert_that(it.children[1].kind, is_("SimpleWhitespace"))
        assert_that(it.children[2].kind, is_("LeftSquareBracket"))
        assert_that(it.children[3].kind, is_("SubscriptElement"))
        assert_that(it.children[4].kind, is_("RightSquareBracket"))

    def test_named_expr(self):
        it = self.pattern_factory.create_statement("if n:= len(items): pass")
        assert_that(it.children[1].kind, is_("NamedExpr"))

    def test_starred(self):
        it = self.pattern_factory.create_statement("*x =[1,2]")
        assert_that(it.children[0].children[0].kind, is_("StarredElement"))

    def test_formatted_value(self):
        it = self.pattern_factory.create_expression('f"{one}two"')
        assert_that(it.children[0].kind, is_("FormattedStringExpression"))

    def test_except_handler(self):
        it = self.pattern_factory.create_statement("try: pass\nexcept NameError:pass")
        assert_that(it.children[2].kind, is_("ExceptHandler"))

    @pytest.mark.parametrize(
        "raw, kind",
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
    )
    def test_comperator_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(it.children[1].children[0].kind, is_(kind))

    @pytest.mark.parametrize(
        "raw, kind",
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
                "MatchList",
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
    )
    def test_match_patterns(self, raw, kind):
        sample_code = f"match data:\n  {raw}\n  case _: pass"
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(stmt.children[4].children[1].kind, is_(kind))

    def test_match_stmt(self):
        sample_code = (
            'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        )
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(stmt.kind, is_("Match"))
        assert_that(stmt.children[4].children[1].kind, is_("MatchList"))
        assert_that(stmt.children[4].children[1].children[2].kind, is_("MatchStar"))
        assert_that(stmt.children[5].children[1].kind, is_("MatchAs"))

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("a % b", "Modulo"),
            ("a / b", "Divide"),
            ("a // b", "FloorDivide"),
            ("a << b", "LeftShift"),
            ("a >> b", "RightShift"),
            ("a * b", "Multiply"),
            ("a ** b", "Power"),
            ("a - b", "Subtract"),
            ("a + b", "Add"),
        ],
    )
    # @pytest.mark.skip("wrong definition")
    def test_binary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(it.children[1].kind, is_(kind))

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

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("+b", "Plus"),
            ("-b", "Minus"),
            ("~b", "BitInvert"),
            ("not b", "Not"),
        ],
    )
    def test_unary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(it.kind, is_("UnaryOperation"))
        assert_that(it.children[0].kind, is_(kind))

    def test_show_call(self):

        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "apple.py")
        second_stmt = atu.children[1]
        assert_that(second_stmt.offset, is_(7))
        assert_that(second_stmt.length, is_(8))
        assert_that(second_stmt.filename, is_("apple.py"))
        assert_that(atu.translation_unit, is_(second_stmt.translation_unit))

    def test_attribute_signature_has_at(self):
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[0]
        assert_that(attr.signature, is_("@TUAT\n"))

    def test_node_family(self):
        src = PythonCstNode.load_from_text(
            textwrap.dedent("""
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
            """),
            "nav.py",
        )
        #          module  class     body        fun memem
        me = src.children[-1].children[5].children[2]
        assert_that(me.name, is_("mememe"))
        assert_that(me.preceding_sibling.name, is_("previous_me"))
        assert_that(me.next_sibling.name, is_("next_me"))
        assert_that(me.parent.parent.name, is_("Parent"))
        # all children are mashed together
        assert_that(me.children, has_length(8))

    def test_load_file_with_ignored_types(self):
        atu = PythonCstNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit, is_not(None))

    def test_load_file(self):
        atu = PythonCstNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu, is_not(None))

    def test_load_invalid_file(self):
        with pytest.raises(ParserSyntaxError, match="Syntax Error"):
            PythonCstNode.load(Path(targets.__file__).parent / "invalid.py")

    def test_ann_fun_to_str2(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    
        matches = match_pattern( func_body.children,patterns)
    
        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonCstNode.load_from_text(ann_fun, "fun.py").children[-1]
        assert_that(it.offset, is_(1))
        assert_that(it.signature, contains_string("@parameterized.expand"))

    def test_ann_fun_to_str(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    
        matches = match_pattern( func_body.children,patterns)
    
        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonCstNode.load_from_text(ann_fun, "fun.py").children[-1]
        assert_that(it.signature, contains_string("def test"))


class TestGuardRewritable:
    pass
    # @ignore
    # def test_text_equals_to_binary_content(self):
    #     code = textwrap.dedent("""
    #     @parameterized.expand(Factories.extend(['$x;$y;']))
    #     def test(_):
    #         atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    #         matches = match_pattern( func_body.children,patterns)
    #         self.assert_matches( expected_dicts_per_match,matches)
    #         """)
    #     it = PythonCstNode.load_from_text(code, "fun.py", [], None).body[-1]
    #     expected = it.binary_file_content()[it.offset: it.extended_end_offset]
    #     assert_that(it.text, is_(expected))
