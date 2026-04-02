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
)

import targets
from renaissance.impl.python.rst_node import PythonASTNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree import ASTShower
from renaissance.utils.node_util import traverse
from utils_for_tests import show_node


class TestPythonASTNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonASTNode)
        self.atu = self.factory.create_from_text("a = 0", "all.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        self.pattern_factory = PythonPatternFactory(self.factory)

    @pytest.mark.parametrize(
        "raw, kind",
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
    )
    def test_stmt_kind(self, raw, kind):
        it = self.pattern_factory.create_statement(raw)
        assert_that(kind, is_(it.kind))

    @pytest.mark.parametrize(
        "raw, kind",
        [
            ("with open() as c: pass", "With"),
            ("await (fun(2))", "Await"),
            ("a = 5 + 3", "BinOp"),
            ("0x01 & 0x10", "BitAnd" ""),
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
    )
    def test_stmt_kind_in_context(self, raw, kind):
        it = self.factory.create_from_text(raw, "context.py")
        kinds = [node.kind for node in traverse(it)]
        assert_that(kind, is_in(kinds))

    def test_global_stmt(self):
        it = self.factory.create_from_text("global x", "context.py").body[-1]
        assert_that(it.kind , is_("Global"))
        assert_that(it.kind, is_("Global"))

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
            ("x = (n*2 for n in[1,2])", "GeneratorExp"),
            ('f"{one}two"', "JoinedStr"),
            ("items[1:4]", "Subscript"),
            ("(9, 10)", "Tuple"),
            ("x = not True", "UnaryOp"),
            ("yield fun", "Yield"),
            ("yield from [1,2]", "YieldFrom"),
            ("x = z if z>y else y", "IfExp"),
        ],
    )
    def test_expr_kind(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(kind, is_(it.kind))

    # @pytest.mark.skip("it was working before")
    def test_type_alias(self):
        it = self.factory.create_from_text("type UserId = int", "context.py")
        show_node(it)
        kinds = [node.kind for node in traverse(it)]
        assert_that("TypeAlias", is_in(kinds))

    def test_slice(self):
        it = self.pattern_factory.create_expression("items[1:2:3]")
        assert_that(it.children[1].kind, is_("Slice"))

    def test_named_expr(self):
        it = self.pattern_factory.create_statement("if n:= len(items): pass")
        assert_that(it.children[0].kind, is_("NamedExpr"))

    def test_starred(self):
        it = self.pattern_factory.create_statement("*x =[1,2]")
        assert_that(it.children[0].children[0].kind, is_("Starred"))

    def test_formatted_value(self):
        it = self.pattern_factory.create_expression('f"{one}two"')
        assert_that(it.children[0].kind, is_("FormattedValue"))

    def test_except_handler(self):
        it = self.pattern_factory.create_statement("try: pass\nexcept NameError:pass")
        assert_that(it.children[1].children[0].kind, is_("ExceptHandler"))

    @pytest.mark.parametrize(
        "raw, kind",
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
    )
    def test_match_patterns(self, raw, kind):
        sample_code = f"match data:\n  {raw}\n  case _: pass"
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(kind, is_(stmt.children[1].children[0].children[0].kind))

    def test_match_stmt(self):
        sample_code = (
            'match data:\n  case [first, *rest]: return f"List with first element {first} and {len(rest)} more items"\n  case _: pass'
        )
        stmt = self.pattern_factory.create_statement(sample_code)
        assert_that(stmt.kind, is_("Match"))
        assert_that(stmt.children[1].children[0].kind, is_("match_case"))
        assert_that(stmt.children[1].children[0].children[0].children[1].kind, is_("MatchStar"))
        assert_that(stmt.children[1].children[0].children[0].children[0].kind, is_("MatchAs"))

    @pytest.mark.parametrize(
        "raw, kind",
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
    )
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
            ("+b", "UAdd"),
            ("-b", "USub"),
            ("~b", "Invert"),
            ("not b", "Not"),
        ],
    )
    def test_unary_operator(self, raw, kind):
        it = self.pattern_factory.create_expression(raw)
        assert_that(it.children[0].kind, is_(kind))

    def test_show_call(self):
        atu = factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "apple.py")
        second_stmt = atu.children[1]
        assert_that(second_stmt.offset, is_(7))
        assert_that(second_stmt.length, is_(7))
        assert_that(second_stmt.filename, is_("apple.py"))
        assert_that(atu.translation_unit, is_(second_stmt.translation_unit))

    def test_attribute_signature_has_at(self):
        src = self.pattern_factory.create_statement("@TUAT\ndef ba(): pass")
        ASTShower.show_node(src)
        attr = src.children[2].children[0]
        assert_that(attr.signature, is_("@TUAT"))

    def test_node_family(self):
        src = PythonASTNode.load_from_text(textwrap.dedent(
            """
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
    """)    )
        #          module  class     body        fun memem
        me = src.children[-1].children[2].children[1]
        assert_that(me.name, is_("mememe"))
        assert_that(me.preceding_sibling.name, is_("previous_me"))
        assert_that(me.next_sibling.name, is_("next_me"))
        assert_that(me.parent.parent.name, is_("Parent"))
        assert_that(me.children[1].children, has_length(4))
    def test_load_file_with_ignored_types(self):
        atu = PythonASTNode.load_from_text("x = 1 # type: ignore", "bogus.py")
        assert_that(atu.translation_unit.atu.type_ignores, has_length(1))
    
    
    
    def test_load_file(self):
        atu = PythonASTNode.load(Path(targets.__file__).parent / "demo.py")
        assert_that(atu.translation_unit.atu.type_ignores, is_(empty()))
    
    
    
    def test_load_invalid_file(self):
        with pytest.raises(IndentationError, match="unexpected indent"):
            PythonASTNode.load(Path(targets.__file__).parent / "invalid.py")
    
    
    
    def test_ann_fun_to_str2(self):
        ann_fun = textwrap.dedent("""
    @parameterized.expand(Factories.extend(['$x;$y;']))
    def test(_):
        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
    
        matches = match_pattern( func_body.children,patterns)
    
        self.assert_matches( expected_dicts_per_match,matches)
        """)
        it = PythonASTNode.load_from_text(ann_fun).body[-1]
        assert_that(it.offset, is_(1))
        assert_that(it.signature, contains_string("@parameterized.expand"))
    
    
    
    # @pytest.mark.skip("it was working before")
    def test_ann_fun_to_str(self):
        ann_fun = textwrap.dedent("""
        @parameterized.expand(Factories.extend(['$x;$y;']))
        def test(_):
            atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
        
            matches = match_pattern( func_body.children,patterns)
        
            self.assert_matches( expected_dicts_per_match,matches)
            """)
        it = PythonASTNode.load_from_text(ann_fun).body[-1]

        assert_that('\n'+it.signature+'\n', is_(ann_fun))

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
    #     it = PythonASTNode.load_from_text(code, "fun.py", [], None).body[-1]
    #     expected = it.binary_file_content()[it.offset: it.extended_end_offset]
    #     assert_that(it.text, is_(expected))









