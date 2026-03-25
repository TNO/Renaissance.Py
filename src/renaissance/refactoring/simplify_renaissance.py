from renaissance.refactoring.PythonRefactoring import PythonRefactoring


class SimplifyRenaissance(PythonRefactoring):
    def __init__(self, file):
        super().__init__(file)

    def simplify(self):
        print(f"simplify {self.file}")
        self.replace("unittest.main()", "pytest.main()")
        self.replace("import unittest", "import pytest\nfrom hamcrest import *")
        self.replace(
            "factory = ASTFactory(PythonASTNode)\n$atu = factory.create_from_text($code, $name)",
            "PythonASTNode.load_from_text($code, $name)",
        )
