#!/usr/bin/env python3
import fnmatch
import sys
from pathlib import Path

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTFactory

factory = ASTFactory(PythonRstNode, [])


def list_matching_files(root: str | Path, recursive: bool = True) -> list[Path]:
    patterns = ["*_unittest.py", "*_test.py", "*_stubs.py"]
    root = Path(root)
    candidates = root.rglob("*.py") if recursive else root.glob("*.py")
    return [p for p in candidates if any(fnmatch.fnmatch(p.name, pat) for pat in patterns)]


def refactor():
    if sys.argv[1] == "refactor":
        print(f"Refactor {Path().resolve()}")
        for file in PythonScanner().find_sources():
            refactoring = sys.argv[2]
            PythonRefactoring.process(refactoring, file)


if __name__ == "__main__":
    refactor()
