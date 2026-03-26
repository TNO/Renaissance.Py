from pathlib import Path

from renaissance.refactoring.python_refactoring import PythonRefactoring


class SimplifyRenaissance(PythonRefactoring):

    def __init__(self, file):
        super().__init__(file)
        self.white_list_patern = 'unit2pytest'
        self.black_list_patern = 'SimplifyRenaissance'
    def process(self):
        print(f"simplify {self.filename}")
        if (self.black_list_patern in self.filename
         or self.white_list_patern not in self.filename):
            print(f"skipping:         {Path(self.filename).resolve()}")
            return

        self.replace("$val = match.expansions[$key][0].signature", "$val= match[$key]")
        self.replace("factory = ASTFactory(PythonASTNode)\n$atu = factory.create_from_text($code, $name)",
            "PythonASTNode.load_from_text($code, $name)",
        )
