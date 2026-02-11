import unittest
from parameterized import parameterized
from refactoring import TautRefactoring
from python.factories import Factories
from syntax_tree import ASTFactory, ASTShower, ASTProcessor


class TestTaut2Unittest(unittest.TestCase):

    @parameterized.expand(Factories.extend([
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ]))
    def test_remove_import_taut(self, _, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, 'import.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        TautRefactoring.remove_import_taut(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        self.assertEqual(result, expected_code)

    @parameterized.expand(Factories.extend([
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ]))
    def test_remove_import(self, _, factory: ASTFactory, input_code, expected_code):
        result = TautRefactoring.convert_test_cases(input_code)
        self.assertEqual(result, expected_code)

    @parameterized.expand(Factories.extend([
        ("class ATestCase(TAUT.TestCase):\n    pass", "class ATestCase(unittest.TestCase):\n    pass\n        "),
    ]))
    def test_replace_taut(self, _, factory: ASTFactory, input_code, expected_code):
        result = TautRefactoring.replace_taut(input_code)
        self.assertEqual(result, expected_code)