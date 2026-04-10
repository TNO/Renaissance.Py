import pytest
from hamcrest import *

from c_cpp.factories import Factories
from renaissance.refactoring import CleanupRefactoring
from renaissance.syntax_tree import ASTShower, ASTFactory, ASTProcessor



class TestCleanupRefactoring:

    @pytest.mark.parametrize(
        "name, factory, input_code, expected_code",
        list(
            Factories.extend(
                [
                    (
                        "int foo() {\n    int x = 1;\n    return 2;\n}",
                        "int foo() {\n    return 2;\n}",
                    ),
                    (
                        "int bar() {\n    int y = 2;\n    int z = y + 3;\n    return z;\n}",
                        "int bar() {\n    int y = 2;\n    int z = y + 3;\n    return z;\n}",
                    ),
                    (
                        "int baz() {\n    int a = 1;\n    int b = 2;\n    int c = a + b;\n    return c;\n}",
                        "int baz() {\n    int a = 1;\n    int b = 2;\n    int c = a + b;\n    return c;\n}",
                    ),
                ]
            )
        ),
    )
    def test_remove_unused_variables(self, name, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, "test.c")
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        CleanupRefactoring.remove_unused_variables(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert_that(result, is_(expected_code))

    def test_should_not_be_instantiable(self):
        assert_that(calling(CleanupRefactoring), raises(Exception))


if __name__ == "__main__":
    pytest.main()
