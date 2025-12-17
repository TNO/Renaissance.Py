from adapters.clang_adapter import ClangAdapter

adapter = ClangAdapter()
lst = adapter.parse("examples/cpp_example.cpp")

for node in lst.traverse():
    print(node)
