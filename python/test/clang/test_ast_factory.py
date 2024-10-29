import logging

from unittest import TestCase
from parameterized import parameterized
from test.c_cpp.factories import Factories

class TestASTFactory(TestCase):

    @parameterized.expand(Factories.factories)
    def test_create(self, _, factory):
        return factory.create_from_text('int main() { return 0; }', "test.c")


