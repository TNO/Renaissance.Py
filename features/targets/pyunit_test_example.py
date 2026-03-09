import unittest
from target import fun, act
from target import arrange

class TestExample(unittest.TestCase):
    def setUp(self):
        self.arrage_1 = Arrang()
        self.arrage_2 = 2

    def test_fun(self):
        self.arrage_1.prepare()
        arrange('other stuff')

        actual = act()

        assertEqual(expected , actual )

