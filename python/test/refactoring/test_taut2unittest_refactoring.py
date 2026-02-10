import unittest
from parameterized import parameterized
from refactoring import TautRefactoring

class TestTaut2Unittest(unittest.TestCase):

    @parameterized.expand([
        ("import TAUT\nimport DDXA", "import DDXA"),
    ])
    def test_remove_import_taut(self, input_code, expected_code):
        result = TautRefactoring.convert_test_cases(input_code)
        self.assertEqual(result, expected_code)