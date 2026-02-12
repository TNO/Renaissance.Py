from unittest import TestCase

class TestExample(TestCase):
    def test_case_example(self):
        # arrange
        factory = {}

        # act
        factory['a']= 1

        # assert
        self.assertEqual(len(factory), 1)
            