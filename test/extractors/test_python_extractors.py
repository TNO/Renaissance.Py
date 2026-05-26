from pathlib import Path

from unittest.mock import MagicMock
from hamcrest import assert_that, is_not, empty

import targets
from renaissance.impl.python.extractor import PythonExtractor


class TestPythonExtractor:

    def test_extractor(self):

        extractor = PythonExtractor()

        assert_that(extractor, is_not(None))

    def test_extract_a_file(self):

        extractor = PythonExtractor()
        extractor.process_file(Path(targets.__file__).parent / "demo.py")

        assert_that(extractor.codebase, is_not(empty()))
        assert_that(extractor.nodes, is_not(empty()))
        assert_that(extractor.edges, is_not(empty()))

    def test_extract_a_file(self):

        extractor = PythonExtractor()
        extractor.process(Path(targets.__file__).parent / "demo.py")
        graphml = Path(targets.__file__).parent / "demo.graphml"
        extractor.save_graph(graphml)
        try:
            with open(graphml, "r") as f:
                content = f.readlines()
                assert_that(content, "demo.graphml")
        finally:
            if graphml.exists():
                graphml.unlink()



#     def test_adds_contains_edge_from_folder_to_file(self):
#         extractor = self._make_extractor()
#         lst = self.make_lst([])
#
#         extractor._process_file("/project/src/foo.py", lst)
#
#         assert_that(extractor.graph.has_edge("/project/src", "/project/src/foo.py"), is_(True))
#         assert_that(extractor.graph.edges["/project/src", "/project/src/foo.py"]["type"], is_("contains"))
#
#     def test_adds_function_node_for_function_definition(self):
#         extractor = self._make_extractor()
#         func_node = make_lst_node("function_definition", "def my_func(x):")
#         lst = self.make_lst([func_node])
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.nodes, has_item("my_func"))
#         assert_that(extractor.graph.nodes["my_func"]["type"], is_("function"))
#
#     def test_adds_defines_edge_for_function(self):
#         extractor = self._make_extractor()
#         func_node = make_lst_node("function_definition", "def my_func(x):")
#         lst = self.make_lst([func_node])
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.has_edge("/src/foo.py", "my_func"), is_(True))
#         assert_that(extractor.graph.edges["/src/foo.py", "my_func"]["type"], is_("defines"))
#
#     def test_adds_call_node_for_call(self):
#         extractor = self._make_extractor()
#         call_node = make_lst_node("call", "some_func(arg1)")
#         lst = self.make_lst([call_node])
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.nodes, has_item("some_func"))
#         assert_that(extractor.graph.nodes["some_func"]["type"], is_("call_target"))
#
#     def test_adds_calls_edge_for_call(self):
#         extractor = self._make_extractor()
#         call_node = make_lst_node("call", "some_func(arg1)")
#         lst = self.make_lst([call_node])
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.has_edge("/src/foo.py", "some_func"), is_(True))
#         assert_that(extractor.graph.edges["/src/foo.py", "some_func"]["type"], is_("calls"))
#
#     def test_ignores_unrelated_node_kinds(self):
#         extractor = self._make_extractor()
#         other_node = make_lst_node("import_statement", "import os")
#         lst = self.make_lst([other_node])
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.nodes, not_(has_item("import os")))
#
#     def test_multiple_functions_all_added(self):
#         extractor = self._make_extractor()
#         nodes = [
#             make_lst_node("function_definition", "def foo(x):"),
#             make_lst_node("function_definition", "def bar(y):"),
#         ]
#         lst = self.make_lst(nodes)
#
#         extractor._process_file("/src/foo.py", lst)
#
#         assert_that(extractor.graph.nodes, has_item("foo"))
#         assert_that(extractor.graph.nodes, has_item("bar"))
#
#
# # ---------------------------------------------------------------------------
# # JavaCodeGraphExtractor
# # ---------------------------------------------------------------------------
#
#
# class TestJavaCodeGraphExtractor(TestBaseCodeGraphExtractor):
#     @staticmethod
#     def _make_extractor():
#         with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
#             return JavaCodeGraphExtractor("java", "fake_lib")
#
#     def test_adds_file_and_folder_nodes(self):
#         extractor = self._make_extractor()
#         lst = self.make_lst([])
#
#         extractor._process_file("/project/src/Main.java", lst)
#
#         assert_that(extractor.graph.nodes, has_item("/project/src/Main.java"))
#         assert_that(extractor.graph.nodes, has_item("/project/src"))
#
#     def test_adds_method_node_for_method_declaration(self):
#         extractor = self._make_extractor()
#         method_node = make_lst_node("method_declaration", "void doSomething()", name="doSomething")
#         lst = self.make_lst([method_node])
#
#         extractor._process_file("/src/Main.java", lst)
#
#         assert_that(extractor.graph.nodes, has_item("doSomething"))
#         assert_that(extractor.graph.nodes["doSomething"]["type"], is_("method"))
#
#     def test_method_node_uses_default_name_when_missing(self):
#         extractor = self._make_extractor()
#         method_node = make_lst_node("method_declaration", "void doSomething()")
#         method_node.properties = {}
#         lst = self.make_lst([method_node])
#
#         extractor._process_file("/src/Main.java", lst)
#
#         assert_that(extractor.graph.nodes, has_item("method"))
#
#     def test_adds_defines_edge_for_method(self):
#         extractor = self._make_extractor()
#         method_node = make_lst_node("method_declaration", "void doSomething()", name="doSomething")
#         lst = self.make_lst([method_node])
#
#         extractor._process_file("/src/Main.java", lst)
#
#         assert_that(extractor.graph.has_edge("/src/Main.java", "doSomething"), is_(True))
#         assert_that(extractor.graph.edges["/src/Main.java", "doSomething"]["type"], is_("defines"))
#
#     def test_adds_method_invocation_node(self):
#         extractor = self._make_extractor()
#         invocation_node = make_lst_node("method_invocation", "obj.doSomething(arg)")
#         lst = self.make_lst([invocation_node])
#
#         extractor._process_file("/src/Main.java", lst)
#
#         assert_that(extractor.graph.nodes, has_item("obj.doSomething"))
#         assert_that(extractor.graph.nodes["obj.doSomething"]["type"], is_("method_target"))
#
#     def test_adds_calls_edge_for_invocation(self):
#         extractor = self._make_extractor()
#         invocation_node = make_lst_node("method_invocation", "obj.doSomething(arg)")
#         lst = self.make_lst([invocation_node])
#
#         extractor._process_file("/src/Main.java", lst)
#
#         assert_that(extractor.graph.has_edge("/src/Main.java", "obj.doSomething"), is_(True))
#         assert_that(extractor.graph.edges["/src/Main.java", "obj.doSomething"]["type"], is_("calls"))
#
#
# # ---------------------------------------------------------------------------
# # CppCodeGraphExtractor
# # ---------------------------------------------------------------------------
#
#
# class TestCppCodeGraphExtractor(TestBaseCodeGraphExtractor):
#     @staticmethod
#     def _make_extractor():
#         with patch("renaissance.extractors.code_graph_extractors.TreeSitterAdapter"):
#             return CppCodeGraphExtractor("cpp", "fake_lib")
#
#     def test_adds_file_and_folder_nodes(self):
#         extractor = self._make_extractor()
#         lst = self.make_lst([])
#
#         extractor._process_file("/project/src/main.cpp", lst)
#
#         assert_that(extractor.graph.nodes, has_item("/project/src/main.cpp"))
#         assert_that(extractor.graph.nodes, has_item("/project/src"))
#
#     def test_adds_function_node_for_function_definition(self):
#         extractor = self._make_extractor()
#         func_node = make_lst_node("function_definition", "int main()", name="main")
#         lst = self.make_lst([func_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.nodes, has_item("main"))
#         assert_that(extractor.graph.nodes["main"]["type"], is_("function"))
#
#     def test_function_node_uses_default_name_when_missing(self):
#         extractor = self._make_extractor()
#         func_node = make_lst_node("function_definition", "int main()")
#         func_node.properties = {}
#         lst = self.make_lst([func_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.nodes, has_item("func"))
#
#     def test_adds_defines_edge_for_function(self):
#         extractor = self._make_extractor()
#         func_node = make_lst_node("function_definition", "int main()", name="main")
#         lst = self.make_lst([func_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.has_edge("/src/main.cpp", "main"), is_(True))
#         assert_that(extractor.graph.edges["/src/main.cpp", "main"]["type"], is_("defines"))
#
#     def test_adds_call_expression_node(self):
#         extractor = self._make_extractor()
#         call_node = make_lst_node("call_expression", "printf(fmt)")
#         lst = self.make_lst([call_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.nodes, has_item("printf"))
#         assert_that(extractor.graph.nodes["printf"]["type"], is_("call_target"))
#
#     def test_adds_calls_edge_for_call_expression(self):
#         extractor = self._make_extractor()
#         call_node = make_lst_node("call_expression", "printf(fmt)")
#         lst = self.make_lst([call_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.has_edge("/src/main.cpp", "printf"), is_(True))
#         assert_that(extractor.graph.edges["/src/main.cpp", "printf"]["type"], is_("calls"))
#
#     def test_ignores_unrelated_node_kinds(self):
#         extractor = self._make_extractor()
#         other_node = make_lst_node("comment", "// a comment")
#         lst = self.make_lst([other_node])
#
#         extractor._process_file("/src/main.cpp", lst)
#
#         assert_that(extractor.graph.nodes, not_(has_item("// a comment")))
#
#
#
