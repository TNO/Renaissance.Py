from unittest import TestCase


class TestExample(TestCase):
    def test_match_all_function_with_any_param_clang(self):
        factory = {'a': 1, 'b': 2}
        self.assertEqual(len(factory), 2)