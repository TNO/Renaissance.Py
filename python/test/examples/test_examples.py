from unittest import TestCase


from examples.refactor_with_nested_compositions import refactor_with_nested_compositions, expected_result

class TestRefactorWithNestedCompositions(TestCase):

    def test_refactor_with_nested_compositions(self):
        result =  refactor_with_nested_compositions(['', ''])
        assert result
        self.assertMultiLineEqual(result, expected_result)
