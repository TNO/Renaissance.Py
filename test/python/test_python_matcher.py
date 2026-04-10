import ast
import textwrap

import pytest
from hamcrest import *
from hamcrest import assert_that, is_not

from renaissance.impl.python import PythonRstNode, PythonPatternFactory
from renaissance.impl.python.factory import PythonFactory
from renaissance.syntax_tree import MatchFinder
from renaissance.syntax_tree.match_finder import (
    is_match,
    match_pattern,
    find_variants,
    INCOMPLETE_MATCH,
    variant_in_match_stmt,
)


class TestPythonMatcher:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_if_statements(self):
        code_if_then_statement =         "if c1:\n    pass"
        code_if_then_else_statement =    "if c1:\n    pass\nelse:   \n    pass"
        code_if_then_elif_statement =    "if c1:\n    pass\nelif c2:\n    pass"
        code_if_then_else_if_statement = "if c1:\n    pass\nelse:\n    if c2:\n        pass"

        if_then_statement = self.pattern_factory.create_statement(code_if_then_statement)
        if_then_else_statement = self.pattern_factory.create_statement(code_if_then_else_statement)
        if_then_elif_statement = self.pattern_factory.create_statement(code_if_then_elif_statement)
        if_then_else_if_statement = self.pattern_factory.create_statement(code_if_then_else_if_statement)

        assert_that(if_then_statement, is_(if_then_statement))
        assert_that(is_match(if_then_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_else_if_statement), is_(False))

        assert_that(if_then_else_statement, is_not(if_then_statement))
        assert_that(is_match(if_then_else_statement, if_then_else_statement), is_(True))
        assert_that(is_match(if_then_else_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_else_statement, if_then_else_if_statement), is_(False))

        assert_that(if_then_elif_statement, is_not(if_then_statement))
        assert_that(is_match(if_then_elif_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_elif_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_elif_statement, if_then_else_if_statement), is_(True))

        assert_that(if_then_else_if_statement, is_not(if_then_statement))
        # assert_that(is_match(if_then_else_if_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_else_if_statement, if_then_else_if_statement), is_(True))


    def test_is_match_if_statements(self):
        code_if_then_statement =         "if c1:\n    pass"
        code_if_then_else_if_statement = "if c1:\n    pass\nelse:\n    if c2:\n        pass"

        if_then_statement = self.pattern_factory.create_statement(code_if_then_statement)
        if_then_else_if_statement = self.pattern_factory.create_statement(code_if_then_else_if_statement)

        assert_that(variant_in_match_stmt(if_then_else_if_statement.children[2], if_then_statement.children[2],{}), is_([]))

    @pytest.mark.parametrize(
        "stmt_txt, pattern_txt, expected",
        [
            # return empty expression list (type None)
            ("return", "return", True),
            ("return", "return $expression_list", False),
            ("return", "return $$expressions", False),
            # TODO discuss whether this is the desired behaviour - empty list
            # return single value
            ("return 1", "return", False),
            ("return 1", "return $expression_list", True),
            ("return 1", "return $$expressions", True),
            # single with trailing separator
            ("return 1,", "return", False),
            ("return 1,", "return $expression_list", True),
            ("return 1,", "return $$expressions", True),
            # multiple
            ("return 1, 2, 3", "return", False),
            ("return 1, 2, 3", "return $expression_list", True),
            ("return 1, 2, 3", "return $$expressions", True),
            # multiple with trailing separator
            ("return 1, 2, 3,", "return", False),
            ("return 1, 2, 3,", "return $expression_list", True),
            ("return 1, 2, 3,", "return $$expressions", True),
        ],
    )
    def test_placeholder_return_stmt(self, stmt_txt: str, pattern_txt: str, expected: bool):
        stmt = self.pattern_factory.create_statement(stmt_txt)
        pattern = self.pattern_factory.create_statement(pattern_txt)
        assert_that(is_match(stmt, pattern), is_(expected))

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

    def test_match_multiple_single_stmt(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        simple = self.pattern_factory.create_statements("$pa")
        result = MatchFinder.match_pattern(atu.children, simple)
        assert_that(result, has_length(4))

    def test_match_fix_stmt_fix_param(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("ca(555)")
        result = MatchFinder.match_pattern(atu.children, simple)
        assert_that(result, has_length(1))

    def test_is_match_any_stmt_with_fix_param_in_detail(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statement("$pa(55)")
        assert_that(is_match(atu.children[0], simple), is_(True))
        assert_that(is_match(atu.children[1], simple), is_(False))
        assert_that(is_match(atu.children[2], simple), is_(False))
        assert_that(is_match(atu.children[3], simple), is_(False))
        result = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(result, has_length(1))

    def test_is_match_any_stmt_with_any_param(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")

        simple = self.pattern_factory.create_statements("$ca($sss)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(3))

    def test_match_multi_fix_stmts(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        simple = self.pattern_factory.create_statements("ba(55)\nca(555)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(1))

    def test_match_fix_stmt_with_multi_result(self):
        atu = self.factory.create_from_text("pa(55)\npa(55)\npa(55)\npa=55", "test.py")
        simple = self.pattern_factory.create_statement("pa(55)")
        results = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(results, has_length(3))

    def test_match_multi_fix_stmt_with_multi_result(self):
        atu = self.factory.create_from_text("ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55")
        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(2))
        assert_that(results[0].nodes, has_length(3))

    def test_match_multi_fix_stmt_with_multi_different_result(self):
        atu = self.factory.create_from_text(
            "ba(51)\nna(52)\nna(53)\npa(54)\npa(55)\nba(56)\nna(57)\nna(58)\nna=59\nba(51)\nna(52)\nna(53)\n"
        )
        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(3))
        assert_that(results[1].nodes, has_length(3))
        assert_that(results[2].nodes, has_length(3))

    def test_match_stmts_in_children(self):
        atu = self.factory.create_from_text(
            "ba(51)\nna(52)\nna(53)\npa(54)\nif pa(55):\n  ba(51)\n  na(52)\n  na(53)\n  na=59\nelse:\n  ba(51)\n  na(52)\n  na(53)\n"
        )
        simple = self.pattern_factory.create_statements("ba($a)\nna($b)\nna($c)")
        results = MatchFinder.match_pattern(atu.children, simple)
        assert_that(results, has_length(3))
        assert_that(results[0].nodes, has_length(3))

    def test_match_placeholder_with_args(self):
        atu = self.factory.create_from_text("ba()\nna()\nba()\npa(54)\nba()\nna()\nba()\nna()\nna=59\nba(1)\nna()\nba(1)")
        simple = self.pattern_factory.create_statements("ba($a)\n$$na\nba($c)")
        results = match_pattern(atu.children, simple)
        assert_that(results, has_length(1))
        assert_that(results[0].nodes, has_length(3))

    def test_match_sandwitch_pattern_with_different_content(self):
        atu = self.factory.create_from_text(textwrap.dedent("""
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
            
            """))

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
    def test_match_all_epxression(self):
        atu = self.factory.create_from_text("pa(55)\npa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55")

        simple = self.pattern_factory.create_expression("pa(55)")
        results = MatchFinder.match_pattern(atu.children, [simple])
        assert_that(results, has_length(6))

    def test_match_all_statement(self):
        atu = self.factory.create_from_text("pa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55")

        simple = self.pattern_factory.create_statements("pa(55)")
        results = match_pattern(atu.children, simple)
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
        atu = self.factory.create_from_text(example_code)
        assert_that(atu, is_not(None))

    def test_find_pattern_four_depth(self):
        example_code = """class CommonTestUtils():
    def foo():
        self.tds = [
            TestDoubles(a=ImprovedStub(read)),
            TestDoubles(b=ImprovedStub(write)),
        ]
        """
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_expression("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(2))

    def test_find_pattern_one_expr(self):
        example_code = textwrap.dedent("""
        [TestDoubles(b=ImprovedStub(write))]
        """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_expression("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(1))

    def test_find_pattern_one_stmt(self):
        example_code = textwrap.dedent("""
        TestDoubles(b=ImprovedStub(write))
        """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statement("TestDoubles($a=ImprovedStub($b))")
        assert_that(match_pattern(atu.children, [pattern]), has_length(1))

    def test_variable_length_match_variant_x(self):
        example_code = textwrap.dedent("0\n1\n2\n3\n4\n5\n3")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n3\n$$after")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(2))
        assert_that(variants[0].end_index, is_(6))
        assert_that(variants[1].end_index, is_(6))


        assert_that(variants[0].exp["$$before"], has_length(6))
        assert_that(variants[0].exp["$$after"], has_length(0))
        assert_that(variants[1].exp["$$before"], has_length(3))
        assert_that(variants[1].exp["$$after"], has_length(3))

    def test_simple_match_with_variant(self):
        example_code = textwrap.dedent("0\n1\n2\n")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("0\n1\n2\n")
        assert_that(find_variants(atu.children, pattern), has_length(1))

    def test_variable_length_matcher_as_valid_variants(self):
        example_code = textwrap.dedent("""
            0
            1
            2
            3
            4
            5
            6
            """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n$mid")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(7))

    def test_variable_length_matcherat_start_end_end_as_variants(self):
        example_code = textwrap.dedent("""
            0
            1
            2
            3
            4
            5
            6
            """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n$mid\n$$after")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(7))

    def test_match_pattern_needs_variants(self):
        example_code = textwrap.dedent("0\n1\n2\n8\n0\n7\n2")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n$mid\n$$after\n8\n$$before\n$dido\n$$after")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(1))
        assert_that(variants[0].exp["$$before"], has_length(1))
        assert_that(variants[0].exp["$mid"], has_length(1))
        assert_that(variants[0].exp["$dido"], has_length(1))
        assert_that(variants[0].exp["$$after"], has_length(1))
        # assert_that(variants[0].exp["$$before"], has_length(0))
        # assert_that(variants[0].exp["$mid"], has_length(1))
        # assert_that(variants[0].exp["$dido"], has_length(1))
        # assert_that(variants[0].exp["$$after"], has_length(0))

    def test_trim_variants(self):
        example_code = textwrap.dedent("0\n1\n2\n8\n0\n7\n2")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n$mid\n$$after\n8\n$$before\n$dito\n$$after")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(1))

    def test_mismatch_with_double_match_all(self):
        example_code = textwrap.dedent("0\n1\n2\n3\n0\n7\n2")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n3\n$$before")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(0))

    def test_trim_variants_with_double_match_all(self):
        example_code = textwrap.dedent("0\n1\n2\n0\n7\n2")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$$before\n$mid\n$$after\n$$before\n$dido\n$$after")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, has_length(3))
        assert_that(variants[2].end_index, is_(2)) # [] 0 [] [] 1 []
        # assert_that(trimmed_variants[1], has_length(3)) # [] 0 [1] [] 2 missing 1
        # assert_that(trimmed_variants[2], has_length(5))

    def test_match_variant_in_args(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_expression("$f($$before, $a, $$after)")
        variants = find_variants(atu.body[0].expression.children[1].children, pattern.children[1].children, {})
        assert_that(variants, has_length(greater_than(1)))

    def test_variant_in_args(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_expression("$f($$before, $a, $$after)")
        variants = variant_in_match_stmt(atu.body[0].expression.children[1], pattern.children[1], {})
        assert_that(variants, has_length(greater_than(1)))

    def test_variant_in_children_function(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)")
        variants = variant_in_match_stmt(atu.body[0], pattern[0], {})
        assert_that(variants, has_length(5))
        assert_that(variants[2].exp["$$before"], has_length(2))
        assert_that(variants[2].exp["$a"][0].signature, is_("3"))
        assert_that(variants[2].exp["$$after"], has_length(2))

    def test_variant_in_children_function_with_expansion(self):

        atu = self.factory.create_from_text("fc(1,2,3,4,5)")
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)")
        variants = variant_in_match_stmt(atu.body[0], pattern[0], {})

        atu = self.factory.create_from_text("fc(1,2,6,4,5)")
        pattern = self.pattern_factory.create_statements("$f($$before, $b, $$after)")
        variants = variant_in_match_stmt(atu.body[0], pattern[0], variants[2].exp)

        assert_that(variants, has_length(1))
        assert_that(variants[0].exp["$b"][0].name, is_("6"))

    def test_find_variant_in_children_function(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)")
        variants = find_variants(atu.body, pattern, {})
        assert_that(variants, has_length(greater_than(1)))

    def test_only_one_variant_in_children_functions(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)\nfc(1,2,6,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)\n$f($$before, $b, $$after)")
        variants = find_variants(atu.body, pattern, {})
        # should be 1
        assert_that(variants, has_length(1))

    def test_variant_in_children(self):
        example_code = textwrap.dedent("fc(1,2,3,4,5)")
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)")
        variants = find_variants(atu.children, pattern)
        print(variants)
        assert_that(variants, has_length(greater_than(1)))

    def test_variable_length_matcher(self):
        example_code = textwrap.dedent("""
            fc(1,2,3,4,5)
            fc(1,2,6,4,5)

            fc(1,2,3,4,5)
            fc_else(1,2,6,4,5)
                """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("$f($$before, $a, $$after)\n$f($$before, $b, $$after)")
        variants = find_variants(atu.children, pattern)
        assert_that(variants, is_not(empty()))
        assert_that(variants, is_not(empty()))
        assert_that(match_pattern(atu.children, pattern), has_length(1))

    def test_match_multi_fun_using_generic_matcher2(self):
        atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        simple = self.pattern_factory.create_statements("ba(55)\nca(555)")
        result = match_pattern(atu.children, simple)
        assert_that(result, has_length(1))


if __name__ == "__main__":
    pytest.main()
