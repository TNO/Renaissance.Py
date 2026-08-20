import os
import networkx
from pathlib import Path
from typing import List

from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter

from renaissance.impl.tree_sitter.factory import TreeStiterPatternFactory
from renaissance.impl.types import *
from renaissance.syntax_tree import PatternMatch
from renaissance.syntax_tree.match_finder import match_pattern

GRAPHML_DIR = "out_graphml"
os.makedirs(GRAPHML_DIR, exist_ok=True)


class Extractor:
    def __init__(self, factory: TreeStiterPatternFactory, patterns: list[str]):
        self.pattern_factory = factory
        self.patterns = patterns

    def run(self, raw: str) -> list[PatternMatch]:
        code = self.pattern_factory.create_statements(raw)
        results = []
        for rule in self.patterns:
            pattern = self.pattern_factory.create_statements(rule)
            results.extend(match_pattern(code, pattern, {}))
        return results


class BaseCodeGraphExtractor:
    def __init__(self, language: str, lib_path: str):
        self.language = language
        self.lib_path = lib_path
        self.adapter = TreeSitterAdapter(lib_path)
        self.graph = networkx.DiGraph()

    def extract(self, files):
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
        networkx.write_graphml(self.graph, path)
        print(f"Graph saved to: {path}")


class PythonCodeGraphExtractor(BaseCodeGraphExtractor):
    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if node.ast_type == FunctionDef:
                name = node.signature.split("(")[0].split()[-1]
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.ast_type == Call:
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
            if node.ast_type == FunctionDef:
                name = node.properties.get("name", "method")
                self.graph.add_node(name, type="method", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.ast_type == Call:
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
            if node.ast_type == FunctionDef:
                name = node.properties.get("name", "func")
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif node.ast_type == Call:
                call_expr = node.signature.strip().split("(")[0]
                self.graph.add_node(call_expr, type="call_target")
                self.graph.add_edge(file_path, call_expr, type="calls")
