import pytest
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from hamcrest import assert_that, empty, greater_than, has_length, is_, is_not

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.lst import LST
from renaissance.utils.ast_utils import traverse


class TestLanguages:
    @pytest.mark.parametrize(
        "lang, code",
        [
            (tspython, "def add(x, y): return x + y"),
            (tspython, "if x > 0:    print(x)"),
            (tspython, "for i in range(10): print(i)"),
            (tspython, "while True: break"),
            (tspython, "try:    x = 1 except:    x = 2"),
            (tspython, "class Foo:    def bar(self): pass"),
            (tspython, "import math"),
            (tspython, "with open('x') as f:    data = f.read()"),
            (tspython, "@decorator def func(): pass"),
            (tspython, "lambda x: x * 2"),
            (tspython, "x = 5"),
            (tspython, "assert x > 0"),
            (tspython, "print('hello')"),
            (tspython, "def outer():    def inner(): pass"),
            (tspython, "raise ValueError('error')"),
            (tspython, "yield x"),
            (tspython, "global x"),
            (tspython, "nonlocal x"),
            (tspython, "pass"),
            (tspython, "continue"),
            #        tsjava
            (tsjava, "public class A {}"),
            (tsjava, "public class A { void m() {} }"),
            (tsjava, "int x = 5;"),
            (tsjava, 'String s = "hi";'),
            (tsjava, "if (x > 0) {}"),
            (tsjava, "for (int i = 0; i < 10; i++) {}"),
            (tsjava, "while (true) {}"),
            (tsjava, "do {} while (false);"),
            (tsjava, "switch (x) { case 1: break; }"),
            (tsjava, "try {} catch (Exception e) {}"),
            (tsjava, "void m() { return; }"),
            (tsjava, "class A { int x; A() {} }"),
            (tsjava, "interface I {}"),
            (tsjava, "enum E { A, B }"),
            (tsjava, "import java.util.*;"),
            (tsjava, "package test;"),
            (tsjava, "@Override void m() {}"),
            (tsjava, "class B extends A {}"),
            (tsjava, "new Object();"),
            (tsjava, 'System.out.println("hi");'),
            # tscpp
            (tscpp, "int main() { return 0; }"),
            (tscpp, "int add(int a, int b) { return a + b; }"),
            (tscpp, "#include <iostream>"),
            (tscpp, "using namespace std;"),
            (tscpp, "class A {};"),
            (tscpp, "struct B { int x; };"),
            (tscpp, "template<typename T> class C {};"),
            (tscpp, "enum Color { RED, GREEN };"),
            (tscpp, "void loop() { for (int i = 0; i < 10; i++) {} }"),
            (tscpp, "if (x > 0) {}"),
            (tscpp, "while (true) {}"),
            (tscpp, "switch (x) { case 1: break; }"),
            (tscpp, "try {} catch (...) {}"),
            (tscpp, "auto f = []() { return 1; };"),
            (tscpp, "int* ptr = nullptr;"),
            (tscpp, 'std::cout << "Hello" << std::endl;'),
            (tscpp, "namespace ns {}"),
            (tscpp, "bool flag = true;"),
            (tscpp, "char c = 'a';"),
            (tscpp, "float pi = 3.14f;"),
        ],
    )
    def test_language_parsing(self, lang, code):
        adapter = TreeSitterAdapter(lang)
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        assert_that(lst, is_(LST))
        nodes = list(traverse(lst.root))
        assert_that(nodes, has_length(greater_than(0)))


if __name__ == "__main__":
    pytest.main()
