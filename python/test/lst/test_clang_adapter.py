import unittest

from impl.clang.clang_adapter import ClangAdapter
from lst.lst import LST
from utils.node_util import traverse


class TestClangAdapter(unittest.TestCase):
    @unittest.skip("don't know what the correct path should be")
    def test_parse_cpp_file(self):
        adapter = ClangAdapter('../../../.venv/Lib/site-packages/clang/native')
        lst = adapter.parse("../../../features/targets/cpp_example.cpp")
        self.assertIsInstance(lst, LST)
        self.assertGreater(len(list(traverse(lst.root))), 0)


if __name__ == "__main__":
    unittest.main()
