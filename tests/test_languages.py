import unittest
from lst.lst import LST
from adapters.tree_sitter_adapter import TreeSitterAdapter

import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava

# Define simple code examples per language
examples = {
    tspython: [
        "def add(x, y): return x + y",
        "if x > 0:    print(x)",
        "for i in range(10): print(i)",
        "while True: break",
        "try:    x = 1 except:    x = 2",
        "class Foo:    def bar(self): pass",
        "import math",
        "with open('x') as f:    data = f.read()",
        "@decorator def func(): pass",
        "lambda x: x * 2",
        "x = 5",
        "assert x > 0",
        "print('hello')",
        "def outer():    def inner(): pass",
        "raise ValueError('error')",
        "yield x",
        "global x",
        "nonlocal x",
        "pass",
        "continue",
    ],
    tsjava: [
        "public class A {}",
        "public class A { void m() {} }",
        "int x = 5;",
        'String s = "hi";',
        "if (x > 0) {}",
        "for (int i = 0; i < 10; i++) {}",
        "while (true) {}",
        "do {} while (false);",
        "switch (x) { case 1: break; }",
        "try {} catch (Exception e) {}",
        "void m() { return; }",
        "class A { int x; A() {} }",
        "interface I {}",
        "enum E { A, B }",
        "import java.util.*;",
        "package test;",
        "@Override void m() {}",
        "class B extends A {}",
        "new Object();",
        'System.out.println("hi");',
    ],
    tscpp: [
        "int main() { return 0; }",
        "int add(int a, int b) { return a + b; }",
        "#include <iostream>",
        "using namespace std;",
        "class A {};",
        "struct B { int x; };",
        "template<typename T> class C {};",
        "enum Color { RED, GREEN };",
        "void loop() { for (int i = 0; i < 10; i++) {} }",
        "if (x > 0) {}",
        "while (true) {}",
        "switch (x) { case 1: break; }",
        "try {} catch (...) {}",
        "auto f = []() { return 1; };",
        "int* ptr = nullptr;",
        'std::cout << "Hello" << std::endl;',
        "namespace ns {}",
        "bool flag = true;",
        "char c = 'a';",
        "float pi = 3.14f;",
    ],
}


class TestLanguages(unittest.TestCase):

    def test_language_parsing(self):
        for lang in examples:
            adapter = TreeSitterAdapter(lang)
            for idx, code in enumerate(examples[lang]):
                with self.subTest(lang=lang, case=idx):
                    tree = adapter.parse_code(code)
                    lst = adapter.to_lst(code, tree)
                    self.assertIsInstance(lst, LST)
                    nodes = list(lst.traverse())
                    self.assertGreater(len(nodes), 0)


if __name__ == "__main__":
    unittest.main()
