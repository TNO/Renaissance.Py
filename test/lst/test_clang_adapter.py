import unittest
from pathlib import Path

import targets
from renaissance.impl.clang.clang_adapter import ClangAdapter
from renaissance.lst.lst import LST
from renaissance.utils.node_util import traverse


class TestClangAdapter(unittest.TestCase):
    def test_parse_cpp_file(self):
        adapter = ClangAdapter() #clang.__file__.replace('__init__.py','native'))

        lst = adapter.parse(Path(targets.__file__).parent / "cpp_example.cpp")
        self.assertIsInstance(lst, LST)
        self.assertGreater(len(list(traverse(lst.root))), 0)


if __name__ == "__main__":
    unittest.main()
