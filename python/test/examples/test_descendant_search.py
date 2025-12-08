from unittest import TestCase
from parameterized import parameterized
from syntax_tree.match_finder import MatchFinder

from examples.descendant_search import find_descendant_match
from test.c_cpp.factories import Factories
from syntax_tree import CPatternFactory, ASTFactory, ASTShower


class TestFindDescendantMatch(TestCase):

    code_text: str = """
            int my_function();
                                       
            void your_function(int count) {
                int z = my_function();
                if (count > my_function()) {
                    int x = my_function();
                    my_function();
                }
                my_function();
                if (count <= my_function()) {
                    int y = my_function();
                } else {
                    my_function();
                }
                my_function();
            }
            """

    outer_text: str = "if ($cond) { $$stmts; }"
    inner_text: str = "my_function()"
    extra_declarations_inner_text: list[str] = ["int my_function();"]
    # inner_text: str = "$f()"
    # extra_declarations_inner_text: list[str] = ["int $f();"]

    @parameterized.expand(Factories.factories)
    def test_descendant_search(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(
            self.inner_text, self.extra_declarations_inner_text
        )
        # ASTShower.show_node(code_pattern)
        # ASTShower.show_node(outer_pattern)
        # ASTShower.show_node(inner_pattern)
        results = find_descendant_match(
            code_pattern, outer_pattern, inner_pattern
        ).to_list()

        # print("========== found =================")
        # for result in results:
        #     ASTShower.show_nodes(result.src_nodes)
        # print("==================================")
        # ASTShower.show_nodes(result.get_nodes()["$f"])
        # ASTShower.show_nodes(result.get_nodes()["$cond"])

        count: int = len(results)
        assert 3 == count, "count = " + str(count)

class TestBasic(TestCase):

    code_text: str = """
            int my_function();
            void your_function() {
                my_function();
            }
            """

    literal_text: str = "my_function()"
    extra_declarations_literal_text: list[str] = ["int my_function();"]
    
    placeholder_text: str = "$f()"
    extra_declarations_placeholder_text: list[str] = ["int $f();"]

    @parameterized.expand(list(Factories.extend([
        (literal_text, extra_declarations_literal_text),
        (placeholder_text, extra_declarations_placeholder_text),
    ])))
    def test_snippet(self, _: str, factory: ASTFactory, snippet: str, extra_declarations: list[str]):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        snippet_pattern = pattern_factory.create_expression(
            snippet, extra_declarations
        )
        results = MatchFinder.find_all(code_pattern, [snippet_pattern]).to_list()
        ASTShower.show_node(code_pattern)
        ASTShower.show_node(snippet_pattern)
        print("========== found =================")
        for result in results:
            ASTShower.show_nodes(result.src_nodes)
        print("==================================")
        count: int = len(results)
        assert 1 == count, "count = " + str(count)