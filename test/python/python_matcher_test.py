import ast
import textwrap
import pytest
from hamcrest import *

from hamcrest import assert_that, is_not

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match, match_pattern


class TestPythonMatcher:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_if_statement(self):
        code_if_then_statement = "if c1:\n    pass"
        code_if_then_else_statement = "if c1:\n    pass\nelse:\n    pass"
        code_if_then_elif_statement = "if c1:\n    pass\nelif c2:\n    pass"
        code_if_then_else_if_statement = "if c1:\n    pass\nelse:\n    if c2:\n        pass"
        
        if_then_statement = self.pattern_factory.create_statement(code_if_then_statement)
        if_then_else_statement = self.pattern_factory.create_statement(code_if_then_else_statement)
        if_then_elif_statement = self.pattern_factory.create_statement(code_if_then_elif_statement)
        if_then_else_if_statement = self.pattern_factory.create_statement(code_if_then_else_if_statement)
        
        assert_that(is_match(if_then_statement, if_then_statement), is_(True))
        assert_that(is_match(if_then_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_else_if_statement), is_(False))

        assert_that(is_match(if_then_else_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_else_statement, if_then_else_statement), is_(True))
        assert_that(is_match(if_then_else_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_else_statement, if_then_else_if_statement), is_(False))

        assert_that(is_match(if_then_elif_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_elif_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_elif_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_elif_statement, if_then_else_if_statement), is_(True))

        assert_that(is_match(if_then_else_if_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_else_if_statement, if_then_else_if_statement), is_(True))

    def test_generic_is_match_any_stmt(self):
        atu = self.factory.create_from_text("ba(55)", "test.py")

        simple = self.pattern_factory.create_statement("$pa(55)")

        assert_that(simple.kind, is_("Expr"))
        assert_that(is_match(atu.children[0], simple, {}), is_(True))

    def test_generic_is_match_any_assignment(self):
        atu = self.factory.create_from_text("na=55", "test.py")

        simple = self.pattern_factory.create_statement("$pa")
        assert_that(simple.kind, is_("_MatchOne__"))
        assert_that(is_match(atu.children[0], simple, {}), is_(True))

    def test_match_stmt_using_generic_matcher(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("$pa")
        result = MatchFinder.match_pattern(atu.children, simple)
        assert_that(result, has_length(4))

    def test_find_all_using_generic_matcher(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statement("$pa(55)")
        assert_that(is_match(atu.children[0], simple), is_(True))
        assert_that(is_match(atu.children[1], simple), is_(False))
        assert_that(is_match(atu.children[2], simple), is_(False))
        assert_that(is_match(atu.children[3], simple), is_(False))
        result = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(result, has_length(1))

    def test_match_one_fun_pattern_using_generic_matcher(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("$ca($sss)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(3))

    def test_match_fun_using_generic_matcher(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("ca(555)")
        result = MatchFinder.match_pattern(atu.children, simple)
        assert_that(result, has_length(1))

    def test_match_multi_fun_using_generic_matcher(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("ba(55)\nca(555)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(1))

    def test_match_multi_fun_using_generic_matcher2(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations

        simple = self.pattern_factory.create_statements("ba(55)\nca(555)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(1))

    def test_match_flat(self):
        atu = self.factory.create_from_text("pa(55)\npa(55)\npa(55)\npa=55", "test.py")

        simple = self.pattern_factory.create_statement("pa(55)")
        results = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(results, has_length(3))

    def test_match_multiple(self):
        atu = self.factory.create_from_text(
            "ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55",
            "test.py",
        )
        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(2))
        assert_that(results[0].nodes, has_length(3))

    def test_match_different_placeholder(self):
        atu = self.factory.create_from_text(
            "ba(51)\nna(52)\nna(53)\npa(54)\npa(55)\nba(56)\nna(57)\nna(58)\nna=59\nba(51)\nna(52)\nna(53)\n",
            "test.py",
        )

        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(3))
        assert_that(results[1].nodes, has_length(3))
        assert_that(results[2].nodes, has_length(3))

    def test_match_recursion_placeholder(self):
        atu = self.factory.create_from_text(
            "ba(51)\nna(52)\nna(53)\npa(54)\nif pa(55):\n  ba(51)\n  na(52)\n  na(53)\n  na=59\nelse:\n  ba(51)\n  na(52)\n  na(53)\n",
            "test.py",
        )

        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(3))

    def test_match_placeholder_with_args(self):
        atu = self.factory.create_from_text(
            "ba()\nna()\nba()\npa(54)\nba()\nna()\nba()\nna()\nna=59\nba(1)\nna()\nba(1)",
            "test.py",
        )

        simple = self.pattern_factory.create_statements("ba($a)\n$$na\nba($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(1))
        assert_that(results[0].nodes, has_length(3))

    def test_match_any_placeholder_but_different_content(self):
        atu = self.factory.create_from_text(
            textwrap.dedent("""
            ba(51)
            na(52)  
            na(52)  
            na(53)
            ba(53)
            pa(54)
            if pa(55):
                ba(51)  
                na(52)  
                na(53)
                ba(53)
                na(53)  
                na=59
            else:  
                ba(51)  
                na(52)  
                ba(53)
            
            """),
            "test.py",
        )

        simple = self.pattern_factory.create_statements("ba($a)\n$$na\nba($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(5))

    def test_match_any_placeholder_but_in_child(self):
        atu = self.factory.create_from_text(
            textwrap.dedent("""
            ba()
            ca()  
            lo()  
            na()
            ba()
            pa()
            if pa():
                ba()  
                ca()  
                lo()
                na()
                na()  
                na=59
            else:  
                ba()  
                na()  
                ba()
            
            """),
            "test.py",
        )

        simple = self.pattern_factory.create_statements("ba()\n$$na\nna()")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(4))
        assert_that(results[1].nodes, has_length(4))
        assert_that(results[2].nodes, has_length(2))

    # can only return one match
    def test_match_all_epression(self): #TODO: typo? 
        atu = self.factory.create_from_text(
            "pa(55)\npa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55",
            "test.py",
        )

        simple = self.pattern_factory.create_statement("pa(55)")    # TODO: why not expression (as in name test case?)
        results = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(results, has_length(4))

    def test_match_all_statement(self):
        atu = self.factory.create_from_text("pa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55", "test.py")

        simple = self.pattern_factory.create_statement("pa(55)")
        results = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(results, has_length(3))

    def test_ast_name(self):
        simple = self.pattern_factory.create_statement("pa(55)")
        assert_that(simple.name, is_("pa(55)"))

    def test_python_ast_name(self):
        simple = ast.parse("pa(55)").body[0]
        assert_that(simple.value.func.id, is_("pa"))

    def test_equal_nodes(self):
        atu = self.factory.create_from_text("pa(55)\nif pa(55):\n  pa(55)\n  pa=55", "test.py")

        simple = self.pattern_factory.create_statement("pa(55)")
        assert_that(simple, is_(atu.children[0]))

    def test_equal_nodes_different_args(self):
        atu = self.factory.create_from_text("pa(55)\nif pa(55):\n  pa(55)\n  pa=55", "test.py")
        simple = self.pattern_factory.create_statement("pa(66)")
        assert_that(simple, is_not(atu.children[0]))

    def test_replace_multiple_different_nodes(self):
        example_code = textwrap.dedent("""
        from module import foo, bar, baz, quux
        ba(51)
        na(52)
        na(53)
        pa(54)
        if pa():
          ba()
        
        if pa(55):
          ba(51)
          na(52)
          na(53)
          na=59
        else:
          ba(51)
          na(52)
          na(53)
        
        """)
        atu = PythonASTNode.load_from_text(example_code)
        assert_that(atu, is_not(None))

    def test_find_pattern_four_depth(self):
        example_code = """class CommonTestUtils():
    def foo():
        self.tds = [
            TestDoubles(a=ImprovedStub(read)),
            TestDoubles(b=ImprovedStub(write)),
        ]
        """
        atu = PythonASTNode.load_from_text(example_code)
        pattern = self.pattern_factory.create_expression("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(2))

    def test_find_pattern_one_expr(self):
        example_code = textwrap.dedent("""
        [TestDoubles(b=ImprovedStub(write))]
        """)
        atu = PythonASTNode.load_from_text(example_code)
        pattern = self.pattern_factory.create_expression("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(1))

    def test_find_pattern_one_stmt(self):
        example_code = textwrap.dedent("""
        TestDoubles(b=ImprovedStub(write))
        """)
        atu = PythonASTNode.load_from_text(example_code)
        pattern = self.pattern_factory.create_statement("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(1))

if __name__ == "__main__":
    pytest.main()
