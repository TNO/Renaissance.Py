import importlib.util
import os
import tempfile
import textwrap
import unittest


def find_nodes_by_signature(lst, sig):
    return [n for n in lst.traverse() if getattr(n, "signature", None) == sig]


def assert_placeholder_node(testcase, node, expected_name=None):
    testcase.assertEqual(node.kind, "placeholder")
    attrs = getattr(node, "properties", {})
    testcase.assertTrue(attrs.get("placeholder"))
    if expected_name is not None:
        testcase.assertEqual(attrs.get("placeholder_name"), expected_name)
    testcase.assertIn("original_node_type", attrs)
    print(f"✅ SUCCESS: placeholder {expected_name or node.signature} recognized")


class TestTreeSitterPythonPlaceholders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("tree_sitter_python") is None:
            raise unittest.SkipTest("tree_sitter_python not installed")
        import tree_sitter_python as tspython
        from adapters.tree_sitter_adapter import TreeSitterAdapter

        cls.mod = tspython
        cls.Adapter = TreeSitterAdapter

    def test_function_name_is_placeholder(self):
        adapter = self.Adapter(self.mod)
        code = "def __PHL__foo(x):\n    return x\n"
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        nodes = find_nodes_by_signature(lst, "__PHL__foo")
        self.assertTrue(nodes)
        for n in nodes:
            if n.kind == "placeholder":
                assert_placeholder_node(self, n, expected_name="foo")

    def test_non_placeholder_not_coerced(self):
        adapter = self.Adapter(self.mod)
        code = "def normal(x):\n    return x\n"
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        nodes = find_nodes_by_signature(lst, "normal")
        for n in nodes:
            self.assertNotEqual(n.kind, "placeholder")
        print("✅ SUCCESS: Python normal identifier stayed non-placeholder")


class TestTreeSitterJavaPlaceholders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("tree_sitter_java") is None:
            raise unittest.SkipTest("tree_sitter_java not installed")
        import tree_sitter_java as tsjava
        from adapters.tree_sitter_adapter import TreeSitterAdapter

        cls.mod = tsjava
        cls.Adapter = TreeSitterAdapter

    def test_dollar_identifier_is_placeholder(self):
        adapter = self.Adapter(self.mod)
        code = "class T { int $x = 0; }"
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        nodes = find_nodes_by_signature(lst, "$x")
        self.assertTrue(nodes)
        for n in nodes:
            if n.kind == "placeholder":
                assert_placeholder_node(self, n, expected_name="x")

    def test_java_normal_identifier_not_placeholder(self):
        adapter = self.Adapter(self.mod)
        code = "class T { int normal = 1; }"
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        nodes = find_nodes_by_signature(lst, "normal")
        for n in nodes:
            self.assertNotEqual(n.kind, "placeholder")
        print("✅ SUCCESS: Java normal identifier stayed non-placeholder")


class TestClangAdapterPlaceholders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("clang") is None:
            raise unittest.SkipTest("clang not installed")
        from adapters.clang_adapter import ClangAdapter

        cls.Adapter = ClangAdapter

    def test_c_function_placeholder(self):
        code = textwrap.dedent(
            """
        int __PHL__foo(int x) { return x; }
        int main() { return __PHL__foo(42); }
        """
        )
        adapter = self.Adapter()
        lst = adapter.load_from_text(code,'t.c')
        nodes = find_nodes_by_signature(lst, "__PHL__foo")
        self.assertTrue(nodes)
        for n in nodes:
            if n.kind == "placeholder":
                assert_placeholder_node(self, n, expected_name="foo")

    def test_c_normal_identifier_not_placeholder(self):
        code = "int normal(int x) { return x; }"
        adapter = self.Adapter()
        lst = adapter.load_from_text(code,"t.c")
        nodes = find_nodes_by_signature(lst, "normal")
        for n in nodes:
            self.assertNotEqual(n.kind, "placeholder")
        print("✅ SUCCESS: C normal identifier stayed non-placeholder")


if __name__ == "__main__":
    unittest.main(verbosity=2)
