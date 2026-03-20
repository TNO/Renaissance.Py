from pathlib import Path

from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.unit2pytest import Unit2Pytest


if __name__ == "__main__":
    print('Refactor {Path(".").resolve()}')
    for file in PythonScanner().find_sources():
        print(Path(file).resolve())
        Unit2Pytest(file).convert_pytest()
        # SimplifyRenaissance(file).simplify()
        # if 'utils_for_tests' not in str(file):


