import sys
from pathlib import Path

from renaissance.impl.python import PythonASTNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.refactoring.simplify_renaissance import SimplifyRenaissance
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTShower

if __name__ == "__main__":
    if sys.argv[1] == "refactor":
        print(f'Refactor {Path(".").resolve()}')
        for file in PythonScanner().find_sources():
            refactor = sys.argv[2]
            PythonRefactoring.for_name(refactor)(file).process()

    if sys.argv[1] == "inspect":
        print(f"inspect {Path(".").resolve()}")
        file = sys.argv[2]
        ASTShower.focus = f"|{sys.argv[3]}"
        atu = PythonASTNode.load(Path(file))
        ASTShower.show_nodes(atu)
