import os
import networkx as nx
from pathlib import Path
from adapters.tree_sitter_adapter import TreeSitterAdapter
from renaissance.extractors.extractor import PatternMatcherInterfaceExtended
from matchers.match import Match
from typing import List

GRAPHML_DIR = "out_graphml"
os.makedirs(GRAPHML_DIR, exist_ok=True)


class BaseCodeGraphExtractor:
    def __init__(self, language: str, lib_path: str):
        self.language = language
        self.lib_path = lib_path
        self.adapter = TreeSitterAdapter(lib_path, language)
        self.interface = PatternMatcherInterfaceExtended(self.adapter)
        self.graph = nx.DiGraph()

    def extract(self, files: List[str]):
        for f in files:
            try:
                code = Path(f).read_text()
                tree = self.adapter.parse_code(code)
                lst = self.adapter.to_lst(code, tree)
                self._process_file(f, lst)
            except Exception as e:
                print(f"Error processing {f}: {e}")

    def _process_file(self, file_path: str, lst):
        raise NotImplementedError

    def save_graph(self, filename: str):
        path = os.path.join(GRAPHML_DIR, filename)
        nx.write_graphml(self.graph, path)
        print(f"Graph saved to: {path}")


class PythonCodeGraphExtractor(BaseCodeGraphExtractor):
    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if node.kind == "function_definition":
                name = node.signature.split("(")[0].split()[-1]
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.kind == "call":
                call_target = node.signature.strip().split("(")[0]
                self.graph.add_node(call_target, type="call_target")
                self.graph.add_edge(file_path, call_target, type="calls")


class JavaCodeGraphExtractor(BaseCodeGraphExtractor):
    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if node.kind == "method_declaration":
                name = node.properties.get("name", "method")
                self.graph.add_node(name, type="method", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.kind == "method_invocation":
                target = node.signature.strip().split("(")[0]
                self.graph.add_node(target, type="method_target")
                self.graph.add_edge(file_path, target, type="calls")


class CppCodeGraphExtractor(BaseCodeGraphExtractor):
    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if node.kind == "function_definition":
                name = node.properties.get("name", "func")
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.kind == "call_expression":
                call_expr = node.signature.strip().split("(")[0]
                self.graph.add_node(call_expr, type="call_target")
                self.graph.add_edge(file_path, call_expr, type="calls")
