from pathlib import Path
from typing import Any, Self, Sequence

from libcst.codegen.gen_type_mapping import module

from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTShower, ASTFinder


class PythonExtractor:
    codebase:dict = {}
    nodes:dict= {}
    edges:list=[]
    def process_file(self, file:Path):
        root  = PythonASTNode.load(file)
        module = root.filename.replace('/', '.').replace('.py', '')
        for stmt in root:
            match stmt.kind:
                case "Import":
                    self.edges.append((root, "imports", stmt.name))
                case "ImportFrom":
                    for alias in stmt.node.names:
                        self.edges.append((module, "imports", f"{stmt.node.module}.{alias.name}"))
                case 'FunctionDef':
                    self.edges.append((module, "definition", f"{module}.{stmt.name}"))
                    self.nodes[f"{module}.{stmt.name}"]= stmt
                case 'ClassDef':
                    self.edges.append((module, "definition", f"{module}.{stmt.name}"))
                    self.nodes[f"{module}.{stmt.name}"] = stmt
                case _: pass


        tu = root.translation_unit
        # ASTShower.show_node(root)
        self.codebase[file] = root
        # tu.lazy_create_refers(root)
        # self.nodes |= tu._nodes
        # self.edges |=tu._references
        # self.edges |= tu._referenced_by