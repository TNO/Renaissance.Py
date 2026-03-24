import pytest
from unittest.mock import MagicMock, patch
from hamcrest import assert_that, is_, has_item, not_, instance_of

from renaissance.extractors.code_graph_extractors import (
    BaseCodeGraphExtractor,
    PythonCodeGraphExtractor,
    JavaCodeGraphExtractor,
    CppCodeGraphExtractor,
)


def make_lst_node(kind, signature, name=None):
    node = MagicMock()
    node.kind = kind
    node.signature = signature
    node.properties = {"name": name} if name else {}
    return node


def make_lst(nodes):
    lst = MagicMock()
    lst.traverse.return_value = nodes
    return lst


# ---------------------------------------------------------------------------
# BaseCodeGraphExtractor
# ---------------------------------------------------------------------------


class TestBaseCodeGraphExtractor:
    def test_is_abstract(self):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            extractor = BaseCodeGraphExtractor.__new__(BaseCodeGraphExtractor)
            extractor.graph = MagicMock()
            with pytest.raises(NotImplementedError):
                extractor._process_file("file.py", MagicMock())

    def test_extract_calls_process_file_for_each_file(self, mocker, tmp_path):
        f1 = tmp_path / "a.py"
        f1.write_text("x = 1")
        f2 = tmp_path / "b.py"
        f2.write_text("y = 2")

        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter") as mock_adapter_cls:
            mock_adapter = mock_adapter_cls.return_value
            mock_adapter.parse_code.return_value = MagicMock()
            mock_adapter.to_lst.return_value = make_lst([])

            extractor = PythonCodeGraphExtractor("python", "fake_lib")
            spy = mocker.patch.object(extractor, "_process_file")

            extractor.extract([str(f1), str(f2)])

            assert_that(spy.call_count, is_(2))

    def test_extract_skips_file_on_error(self, tmp_path):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter") as mock_adapter_cls:
            mock_adapter = mock_adapter_cls.return_value
            mock_adapter.parse_code.side_effect = RuntimeError("parse error")

            extractor = PythonCodeGraphExtractor("python", "fake_lib")
            # Should not raise
            extractor.extract([str(tmp_path / "nonexistent.py")])

    def test_save_graph_writes_file(self, tmp_path, mocker):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            extractor = PythonCodeGraphExtractor("python", "fake_lib")
            mock_write = mocker.patch("renaissance.extractors.code_graph_extractors.nx.write_graphml")
            mocker.patch("renaissance.extractors.code_graph_extractors.GRAPHML_DIR", str(tmp_path))

            extractor.save_graph("test.graphml")

            mock_write.assert_called_once()

    def test_constructor_creates_directed_graph(self):
        import networkx as nx

        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            extractor = PythonCodeGraphExtractor("python", "fake_lib")
            assert_that(extractor.graph, instance_of(nx.DiGraph))


# ---------------------------------------------------------------------------
# PythonCodeGraphExtractor
# ---------------------------------------------------------------------------


class TestPythonCodeGraphExtractor:
    def _make_extractor(self):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            return PythonCodeGraphExtractor("python", "fake_lib")

    def test_adds_file_and_folder_nodes(self):
        extractor = self._make_extractor()
        lst = make_lst([])

        extractor._process_file("/project/src/foo.py", lst)

        assert_that(extractor.graph.nodes, has_item("/project/src/foo.py"))
        assert_that(extractor.graph.nodes, has_item("/project/src"))

    def test_adds_contains_edge_from_folder_to_file(self):
        extractor = self._make_extractor()
        lst = make_lst([])

        extractor._process_file("/project/src/foo.py", lst)

        assert_that(extractor.graph.has_edge("/project/src", "/project/src/foo.py"), is_(True))
        assert_that(extractor.graph.edges["/project/src", "/project/src/foo.py"]["type"], is_("contains"))

    def test_adds_function_node_for_function_definition(self):
        extractor = self._make_extractor()
        func_node = make_lst_node("function_definition", "def my_func(x):")
        lst = make_lst([func_node])

        extractor._process_file("/src/foo.py", lst)

        assert_that(extractor.graph.nodes, has_item("my_func"))
        assert_that(extractor.graph.nodes["my_func"]["type"], is_("function"))

    def test_adds_defines_edge_for_function(self):
        extractor = self._make_extractor()
        func_node = make_lst_node("function_definition", "def my_func(x):")
        lst = make_lst([func_node])

        extractor._process_file("/src/foo.py", lst)

        assert_that(extractor.graph.has_edge("/src/foo.py", "my_func"), is_(True))
        assert_that(extractor.graph.edges["/src/foo.py", "my_func"]["type"], is_("defines"))

    def test_adds_call_node_for_call(self):
        extractor = self._make_extractor()
        call_node = make_lst_node("call", "some_func(arg1)")
        lst = make_lst([call_node])

        extractor._process_file("/src/foo.py", lst)

        assert_that(extractor.graph.nodes, has_item("some_func"))
        assert_that(extractor.graph.nodes["some_func"]["type"], is_("call_target"))

    def test_adds_calls_edge_for_call(self):
        extractor = self._make_extractor()
        call_node = make_lst_node("call", "some_func(arg1)")
        lst = make_lst([call_node])

        extractor._process_file("/src/foo.py", lst)

        assert_that(extractor.graph.has_edge("/src/foo.py", "some_func"), is_(True))
        assert_that(extractor.graph.edges["/src/foo.py", "some_func"]["type"], is_("calls"))

    def test_ignores_unrelated_node_kinds(self):
        extractor = self._make_extractor()
        other_node = make_lst_node("import_statement", "import os")
        lst = make_lst([other_node])

        extractor._process_file("/src/foo.py", lst)

        assert_that(list(extractor.graph.nodes), not_(has_item("import os")))

    def test_multiple_functions_all_added(self):
        extractor = self._make_extractor()
        nodes = [
            make_lst_node("function_definition", "def foo(x):"),
            make_lst_node("function_definition", "def bar(y):"),
        ]
        lst = make_lst(nodes)

        extractor._process_file("/src/foo.py", lst)

        assert_that(extractor.graph.nodes, has_item("foo"))
        assert_that(extractor.graph.nodes, has_item("bar"))


# ---------------------------------------------------------------------------
# JavaCodeGraphExtractor
# ---------------------------------------------------------------------------


class TestJavaCodeGraphExtractor:
    def _make_extractor(self):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            return JavaCodeGraphExtractor("java", "fake_lib")

    def test_adds_file_and_folder_nodes(self):
        extractor = self._make_extractor()
        lst = make_lst([])

        extractor._process_file("/project/src/Main.java", lst)

        assert_that(extractor.graph.nodes, has_item("/project/src/Main.java"))
        assert_that(extractor.graph.nodes, has_item("/project/src"))

    def test_adds_method_node_for_method_declaration(self):
        extractor = self._make_extractor()
        method_node = make_lst_node("method_declaration", "void doSomething()", name="doSomething")
        lst = make_lst([method_node])

        extractor._process_file("/src/Main.java", lst)

        assert_that(extractor.graph.nodes, has_item("doSomething"))
        assert_that(extractor.graph.nodes["doSomething"]["type"], is_("method"))

    def test_method_node_uses_default_name_when_missing(self):
        extractor = self._make_extractor()
        method_node = make_lst_node("method_declaration", "void doSomething()")
        method_node.properties = {}
        lst = make_lst([method_node])

        extractor._process_file("/src/Main.java", lst)

        assert_that(extractor.graph.nodes, has_item("method"))

    def test_adds_defines_edge_for_method(self):
        extractor = self._make_extractor()
        method_node = make_lst_node("method_declaration", "void doSomething()", name="doSomething")
        lst = make_lst([method_node])

        extractor._process_file("/src/Main.java", lst)

        assert_that(extractor.graph.has_edge("/src/Main.java", "doSomething"), is_(True))
        assert_that(extractor.graph.edges["/src/Main.java", "doSomething"]["type"], is_("defines"))

    def test_adds_method_invocation_node(self):
        extractor = self._make_extractor()
        invocation_node = make_lst_node("method_invocation", "obj.doSomething(arg)")
        lst = make_lst([invocation_node])

        extractor._process_file("/src/Main.java", lst)

        assert_that(extractor.graph.nodes, has_item("obj.doSomething"))
        assert_that(extractor.graph.nodes["obj.doSomething"]["type"], is_("method_target"))

    def test_adds_calls_edge_for_invocation(self):
        extractor = self._make_extractor()
        invocation_node = make_lst_node("method_invocation", "obj.doSomething(arg)")
        lst = make_lst([invocation_node])

        extractor._process_file("/src/Main.java", lst)

        assert_that(extractor.graph.has_edge("/src/Main.java", "obj.doSomething"), is_(True))
        assert_that(extractor.graph.edges["/src/Main.java", "obj.doSomething"]["type"], is_("calls"))


# ---------------------------------------------------------------------------
# CppCodeGraphExtractor
# ---------------------------------------------------------------------------


class TestCppCodeGraphExtractor:
    def _make_extractor(self):
        with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
            return CppCodeGraphExtractor("cpp", "fake_lib")

    def test_adds_file_and_folder_nodes(self):
        extractor = self._make_extractor()
        lst = make_lst([])

        extractor._process_file("/project/src/main.cpp", lst)

        assert_that(extractor.graph.nodes, has_item("/project/src/main.cpp"))
        assert_that(extractor.graph.nodes, has_item("/project/src"))

    def test_adds_function_node_for_function_definition(self):
        extractor = self._make_extractor()
        func_node = make_lst_node("function_definition", "int main()", name="main")
        lst = make_lst([func_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(extractor.graph.nodes, has_item("main"))
        assert_that(extractor.graph.nodes["main"]["type"], is_("function"))

    def test_function_node_uses_default_name_when_missing(self):
        extractor = self._make_extractor()
        func_node = make_lst_node("function_definition", "int main()")
        func_node.properties = {}
        lst = make_lst([func_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(extractor.graph.nodes, has_item("func"))

    def test_adds_defines_edge_for_function(self):
        extractor = self._make_extractor()
        func_node = make_lst_node("function_definition", "int main()", name="main")
        lst = make_lst([func_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(extractor.graph.has_edge("/src/main.cpp", "main"), is_(True))
        assert_that(extractor.graph.edges["/src/main.cpp", "main"]["type"], is_("defines"))

    def test_adds_call_expression_node(self):
        extractor = self._make_extractor()
        call_node = make_lst_node("call_expression", "printf(fmt)")
        lst = make_lst([call_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(extractor.graph.nodes, has_item("printf"))
        assert_that(extractor.graph.nodes["printf"]["type"], is_("call_target"))

    def test_adds_calls_edge_for_call_expression(self):
        extractor = self._make_extractor()
        call_node = make_lst_node("call_expression", "printf(fmt)")
        lst = make_lst([call_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(extractor.graph.has_edge("/src/main.cpp", "printf"), is_(True))
        assert_that(extractor.graph.edges["/src/main.cpp", "printf"]["type"], is_("calls"))

    def test_ignores_unrelated_node_kinds(self):
        extractor = self._make_extractor()
        other_node = make_lst_node("comment", "// a comment")
        lst = make_lst([other_node])

        extractor._process_file("/src/main.cpp", lst)

        assert_that(list(extractor.graph.nodes), not_(has_item("// a comment")))
