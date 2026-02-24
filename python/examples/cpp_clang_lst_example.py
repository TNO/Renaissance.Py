from impl.clang.clang_adapter import ClangAdapter
from syntax_tree import ASTShower

# under unix: '.venv/lib/python3.13/site-packages/clang/native'
adapter = ClangAdapter('.venv/lib/site-packages/clang/native')
lst = adapter.parse("features/targets/cpp_example.cpp")

ASTShower.show_node(lst.root)
