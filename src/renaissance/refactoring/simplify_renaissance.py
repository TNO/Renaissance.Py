from pathlib import Path
from typing import override

from renaissance.refactoring.python_refactoring import PythonRefactoring


class SimplifyRenaissance(PythonRefactoring):

    def __init__(self, file):
        super().__init__(file)
        self.white_list_pattern = "unit2pytest"
        self.black_list_pattern = "SimplifyRenaissance"

    @override
    def run(self):
        if self.black_list_pattern in self.filename or self.white_list_pattern not in self.filename:
            print(f"skipping:         {Path(self.filename).resolve()}")
            return

        print(f"simplify          {Path(self.filename).resolve()}")
        self.replace_stmt("$val = match.expansions[$key][0].signature", "$val= match[$key]")
        self.replace_stmt(
            "factory = ASTFactory(PythonASTNode)\n$atu = factory.create_from_text($code, $name)",
            "PythonASTNode.load_from_text($code, $name)",
        )
        self.commit()
