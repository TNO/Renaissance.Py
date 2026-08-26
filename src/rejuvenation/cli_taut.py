#! /usr/bin/python3
import fnmatch
import os
import sys
from pathlib import Path

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTFactory

factory = ASTFactory(PythonRstNode, [])


def get_migrated_path(file_path):
    """Convert a file path to add '_migrated' before the extension.

    Example: 'taut.py' -> 'taut_migrated.py'
    """
    # Split the path into filename and extension
    base, ext = os.path.splitext(file_path)

    # Create the new path with '_migrated' added
    new_path = f"{base}_migrated{ext}"

    return new_path


def list_matching_files(root: str | Path, recursive: bool = True) -> list[Path]:
    patterns = ["*_unittest.py", "*_test.py", "*_stubs.py"]
    root = Path(root)
    candidates = root.rglob("*.py") if recursive else root.glob("*.py")
    return [p for p in candidates if any(fnmatch.fnmatch(p.name, pat) for pat in patterns)]


if __name__ == "__main__":
    if sys.argv[1] == "refactor":
        print(f'Refactor {Path(".").resolve()}')
        for file in PythonScanner().find_sources():
            refactor = sys.argv[2]
            PythonRefactoring.process(refactor, file)
