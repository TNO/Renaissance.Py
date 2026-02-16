from adapters.clang_adapter import ClangAdapter
from syntax_tree import ASTShower


adapter = ClangAdapter('.venv/Lib/site-packages/clang/native')
lst = adapter.parse("features/targets/cpp_example.cpp")

ASTShower.show_node(lst.root)
