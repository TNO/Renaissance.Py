import clang

from impl.clang.clang_adapter import ClangAdapter
from syntax_tree import ASTShower

adapter = ClangAdapter(clang.__file__.replace('__init__.py','native'))
lst = adapter.parse("features/targets/cpp_example.cpp")

ASTShower.show_node(lst.root)
