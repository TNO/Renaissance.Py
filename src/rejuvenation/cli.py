import sys
from pathlib import Path
from typing import Sequence

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.extractor import PythonExtractor
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTShower


def _resolve_refactor_targets(path_arg: str | None) -> Sequence[Path | str]:
    if not path_arg:
        return PythonScanner().find_sources()

    path = Path(path_arg)
    if path.is_dir():
        return sorted(path.rglob("*.py"))
    return [path]

def refactor():
    if sys.argv[1] == "refactor":
        refactoring = sys.argv[2]
        files = _resolve_refactor_targets(sys.argv[3] if len(sys.argv) > 3 else None)
        print(f'Refactor {Path(".").resolve()}')
        for file in files:
            PythonRefactoring.process(refactoring, file)

    if sys.argv[1] == "extract":
        print(f'Extracting {Path(".").resolve()}')
        extractor = PythonExtractor()
        for file in PythonScanner().find_sources():
            filename = sys.argv[2]
            extractor.process(file)
        extractor.save_graph(filename)
    if sys.argv[1] == "inspect":
        print(f"inspect {Path('.').resolve()}")
        file = sys.argv[2]
        ASTShower.focus = f"|{sys.argv[3]}"
        atu = PythonRstNode.load(Path(file))
        ASTShower.show_node(atu)


if __name__ == "__main__":
    refactor()
