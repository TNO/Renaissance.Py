from pathlib import Path

from targets.go.node import GoAstNode


class GoExtractor:
    codebase: dict = {}
    nodes: dict = {}
    edges: dict = {}

    def process_file(self, file: Path):
        root = GoAstNode.load(file)
        tu = root.translation_unit
        tu.lazy_create_refers(root)
        self.codebase[file] = root
        self.nodes |= tu._nodes
        self.edges |= tu._references
        self.edges |= tu._referenced_by
