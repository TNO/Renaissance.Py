from unittest import TestCase
from parameterized import parameterized

from syntax_tree.ast_shower import ASTShower
from examples.descendant_search import find_descendant_match
from test.c_cpp.factories import Factories
from syntax_tree import CPatternFactory, ASTFactory


class TestFindDescendantMatch(TestCase):

    code_text: str = """
            int my_function();
                                       
            int main(int argc, char *argv[]) {
                int z = my_function();
                if (argc > my_function()) {
                    int x = my_function();
                    my_function();
                }
                my_function();
                if (argc <= my_function()) {
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

    @parameterized.expand(Factories.factories)
    def test_descendant_search(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.cpp")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(
            self.inner_text, self.extra_declarations_inner_text
        )
        # ASTShower.show_node(code_pattern)
        ASTShower.show_node(outer_pattern)
        ASTShower.show_node(inner_pattern)
        results = find_descendant_match(code_pattern, outer_pattern, inner_pattern)
        # TODO: why doesn't .collect(list) not work?
        # AttributeError: 'list' object has no attribute 'for_each'

        print("========== found =================")
        results.for_each(lambda match: ASTShower.show_nodes(match.src_nodes))
        print("==================================")

        # TODO: stream is consumed so count is 0
        # count: int = results.count()
        # assert 3 == count, "count = " + str(count)
