"""AI: Extractor that builds a codebase graph of nodes and edges from Go AST files."""

from pathlib import Path

from targets.go.node import GoAstNode


class GoExtractor:
    """AI: Build a codebase graph of nodes and edges by extracting Go AST files."""

    codebase: dict = {}
    nodes: dict = {}
    edges: dict = {}

    def process_file(self, file: Path):
        """AI: Parse a Go source file and merge its nodes and reference edges into the codebase graph."""
        root = GoAstNode.load(file)
        tu = root.translation_unit
        tu.lazy_create_refers(root)
        self.codebase[file] = root
        self.nodes |= tu.nodes
        self.edges |= tu.references
        self.edges |= tu.referenced_by
