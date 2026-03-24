#! /usr/bin/python3
import argparse
import fnmatch
import os
from pathlib import Path

from renaissance.refactoring.taut2pyunit import *
from renaissance.syntax_tree import ASTFactory

factory = ASTFactory(PythonASTNode, [])


def get_migrated_path(file_path):
    """
    Convert a file path to add '_migrated' before the extension.

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


def refactor():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run my_function from the command line")

    # Add arguments corresponding to your function parameters
    parser.add_argument("path", help="file to migrate")

    # Parse arguments
    args = parser.parse_args()

    unittest_files = []

    path = os.path.abspath(args.path)
    if os.path.isdir(path):
        unittest_files = list_matching_files(path, recursive=True)
    if os.path.isfile(path):
        filename = os.path.basename(path)
        if "_unittest.py" in filename and filename.endswith(".py"):
            unittest_files.append(path)

    for file_path in unittest_files:
        try:
            result = convert_taut_to_unittest(file_path, get_migrated_path(file_path))
            # result = insert_doc(result, "01-22-2026")
            with open(get_migrated_path(file_path), "w") as f:
                f.write(result)
                # print(result)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")


if __name__ == "__main__":
    refactor()
