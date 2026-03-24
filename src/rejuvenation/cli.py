import sys
from pathlib import Path

from renaissance.impl.python import PythonASTNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTShower

if __name__ == "__main__":
    if sys.argv[1] == 'refactor':
        print('Refactor {Path(".").resolve()}')
        for file in PythonScanner().find_sources():
            if 'utils_for_tests' not in str(file):
                print(f"start refactoring {Path(file).resolve()}")
                Unit2Pytest(file).convert_pytest()
            else:
                print(f"skipping:         {Path(file).resolve()}")
        # SimplifyRenaissance(file).simplify()
    if sys.argv[1] == 'inspect':
        print(f"inspect {Path(".").resolve()}")
        file = sys.argv[2]
        ASTShower.focus = f'|{sys.argv[3]}'
        atu = PythonASTNode.load(file)
        ASTShower.show_nodes(atu)