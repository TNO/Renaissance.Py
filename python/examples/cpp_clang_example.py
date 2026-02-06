from adapters.clang_adapter import ClangAdapter


adapter = ClangAdapter()
lst = adapter.parse("features/targets/cpp_example.cpp")

# ASTShower.show_node(lst)
# for node in ASTProcessor.traverse(lst):
#     print(node)
