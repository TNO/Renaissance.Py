import unittest
from adapters.clang_adapter import ClangAdapter
from lst.lst import LST


class TestClangAdapter(unittest.TestCase):
    def test_parse_cpp_file(self):
        adapter = ClangAdapter()
        lst = adapter.parse("../../examples/cpp_example.cpp")
        self.assertIsInstance(lst, LST)
        self.assertGreater(len(list(lst.traverse())), 0)


if __name__ == "__main__":
    unittest.main()
