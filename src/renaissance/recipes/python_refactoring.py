import importlib
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from termcolor import colored

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.python.ast.util import to_str
from renaissance.syntax_tree import ASTProcessor
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.text_utils import snake_case


class PythonRefactoring(ASTProcessor):
    def __init__(self, file):
        factory = PythonFactory(PythonRstNode)
        atu = factory.create(file)
        super().__init__(atu, factory, False)
        self.pattern_factory = PythonPatternFactory(self.factory)
        self.black_list_pattern = ".git"
        self.white_list_pattern = ""

    def replace_stmt(self, find, repl):
        pattern = self.pattern_factory.create_statements(find)
        for match in match_pattern(self.root.children, pattern):
            replacement = repl
            for exp in match.expansions:
                arg_str = ", ".join([to_str(node) for node in match.expansions[exp]])
                replacement = replacement.replace(exp, arg_str)

            replacement = replacement.replace(" ,)", ")").replace(", )", ")")
            self.replace(replacement, match.nodes, False, False)

    @staticmethod
    def process(class_name, file):
        """Return a subclass by name using importlib, like Java's Class.forName()."""
        snake = snake_case(class_name)
        module = importlib.import_module(f"renaissance.recipes.{snake}")
        cls = getattr(module, class_name)
        refactor = cls(file)
        if refactor.black_list_pattern in refactor.filename or refactor.white_list_pattern not in refactor.filename:
            print(f"skipping:         {Path(refactor.filename).resolve()}")
            return

        print(colored(f"refactor          {Path(refactor.filename).resolve()}", "green", attrs=["bold"]))
        refactor.run()

    @property
    def body(self) -> Sequence[PythonRstNode]:
        return cast("PythonRstNode", cast("object", self.root)).body

    def run(self):
        pass
