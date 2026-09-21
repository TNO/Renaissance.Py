"""AI: Extractor that builds a codebase graph from tree-sitter-matched patterns."""

from pathlib import Path

import networkx as nx

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.factory import TreeSitterPatternFactory
from renaissance.syntax_tree import PatternMatch
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.syntax_tree.semantic_kind import SemanticKind

GRAPHML_DIR = "out_graphml"
Path(GRAPHML_DIR).mkdir(parents=True, exist_ok=True)


def _has_semantic_kind(node, kind: SemanticKind) -> bool:
    return node.semantic_kind is kind


class Extractor:
    """AI: Find occurrences of a set of patterns in tree-sitter-parsed code."""

    def __init__(self, factory: TreeSitterPatternFactory, patterns: list[str]):
        """AI: Configure an extractor that finds occurrences of the given patterns in code."""
        self.pattern_factory = factory
        self.patterns = patterns

    def run(self, raw: str) -> list[PatternMatch]:
        """AI: Find occurrences of the configured patterns in raw code and return the matches."""
        code = self.pattern_factory.create_statements(raw)
        results = []
        for rule in self.patterns:
            pattern = self.pattern_factory.create_statements(rule)
            results.extend(match_pattern(code, pattern, {}))
        return results


class BaseCodeGraphExtractor:
    """AI: Base class that extracts a code graph from a language's tree-sitter-parsed files."""

    def __init__(self, language: str, lib_path: str):
        """AI: Configure a code-graph extractor for the given language and grammar library."""
        self.language = language
        self.lib_path = lib_path
        self.adapter = TreeSitterAdapter(lib_path)
        self.graph = nx.DiGraph()

    def extract(self, files):
        """AI: Parse each file and build the code graph by processing its LST."""
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
        """AI: Write the extracted code graph to a GraphML file named filename."""
        path = Path(GRAPHML_DIR) / filename
        nx.write_graphml(self.graph, path)
        print(f"Graph saved to: {path}")


class PythonCodeGraphExtractor(BaseCodeGraphExtractor):
    """AI: Extract a code graph (functions, calls) from Python source files."""

    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if _has_semantic_kind(node, SemanticKind.FUNCTION):
                name = node.signature.split("(")[0].split()[-1]
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif _has_semantic_kind(node, SemanticKind.CALL):
                call_target = node.signature.strip().split("(")[0]
                self.graph.add_node(call_target, type="call_target")
                self.graph.add_edge(file_path, call_target, type="calls")


class JavaCodeGraphExtractor(BaseCodeGraphExtractor):
    """AI: Extract a code graph (methods, calls) from Java source files."""

    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if _has_semantic_kind(node, SemanticKind.FUNCTION):
                name = node.properties.get("name", "method")
                self.graph.add_node(name, type="method", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif _has_semantic_kind(node, SemanticKind.CALL):
                target = node.signature.strip().split("(")[0]
                self.graph.add_node(target, type="method_target")
                self.graph.add_edge(file_path, target, type="calls")


class CppCodeGraphExtractor(BaseCodeGraphExtractor):
    """AI: Extract a code graph (functions, calls) from C++ source files."""

    def _process_file(self, file_path, lst):
        folder = str(Path(file_path).parent)
        self.graph.add_node(file_path, type="file", folder=folder)
        self.graph.add_node(folder, type="folder")
        self.graph.add_edge(folder, file_path, type="contains")

        for node in lst.traverse():
            if _has_semantic_kind(node, SemanticKind.FUNCTION):
                name = node.properties.get("name", "func")
                self.graph.add_node(name, type="function", file=file_path)
                self.graph.add_edge(file_path, name, type="defines")

            elif _has_semantic_kind(node, SemanticKind.CALL):
                call_expr = node.signature.strip().split("(")[0]
                self.graph.add_node(call_expr, type="call_target")
                self.graph.add_edge(file_path, call_expr, type="calls")
