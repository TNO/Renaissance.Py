"""Base class every Python recipe (TypeVarCheck, TypeVarTupleCheck, etc.) extends."""

import ast
import importlib
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from termcolor import colored

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.util import to_str
from renaissance.syntax_tree import ASTProcessor
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.text_utils import snake_case


def narrowed_import_text(raw: ast.ImportFrom, names: str | set[str]) -> str | None:
    """Build the "from module import ..." text for `raw` with `names`' aliases dropped.

    Returns None if nothing would remain (meaning the whole import statement should be removed
    instead).
    """
    targets = {names} if isinstance(names, str) else names
    remaining = [
        alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
        for alias in raw.names
        if (alias.asname or alias.name) not in targets
    ]
    return f"from {raw.module} import {', '.join(remaining)}" if remaining else None


class PythonRefactoring(ASTProcessor):
    """Base class for a Python-source-rewriting recipe.

    Parses a file, exposes helpers to find and rewrite nodes, and dispatches by name via
    process().
    """

    def __init__(self, file):
        """Parse file into an RST tree via PythonFactory.

        Sets up the base ASTProcessor plus the pattern factory replace_stmt() uses.
        """
        factory = PythonFactory(PythonRstNode)
        atu = factory.create(file)
        super().__init__(atu, factory, False)
        self.pattern_factory = PythonPatternFactory(self.factory)
        self.black_list_pattern = ".git"
        self.white_list_pattern = ""

    def replace_stmt(self, find, repl):
        """Replace every statement matching the find pattern with repl.

        Substitutes each of the pattern's expansion placeholders (e.g. `$args`) into repl's text
        before replacing.
        """
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
        module = importlib.import_module(f"renaissance.refactoring.{snake}")
        cls = getattr(module, class_name)
        refactor = cls(file)
        if refactor.black_list_pattern in refactor.filename or refactor.white_list_pattern not in refactor.filename:
            print(f"skipping:         {Path(refactor.filename).resolve()}")
            return

        print(colored(f"refactor          {Path(refactor.filename).resolve()}", "green", attrs=["bold"]))
        refactor.run()

    @property
    def body(self) -> Sequence[PythonRstNode]:
        """The direct child statement nodes of the file's root RST node."""
        return cast("PythonRstNode", cast("object", self.root)).body

    def find_rst_node(self, target: ast.AST) -> Any:
        """Locate the PythonRstNode wrapping a raw ast node.

        E.g. after mutating an ast.FunctionDef in place, this finds the RST node to pass to
        self.replace().
        """
        found: list[Any] = []

        def visit(node: Any) -> None:
            if node.node is target:
                found.append(node)

        self.root.process(visit)
        return found[0]

    def remove_import_alias(self, names: str | set[str]) -> None:
        """Narrow or remove every ast.ImportFrom in self.body whose aliases include any of `names`.

        E.g. once nothing in the file still calls the "TypeVar" it imported. Does nothing to an
        import with none of `names`; deciding whether a name is still needed is the caller's
        responsibility.

        TODO: this narrows/removes one import statement per call, folding every one of `names`
        into a single edit, specifically so that removing several names sharing one import never
        queues two separate edits against the same node - that corrupts the output instead of
        merging, a bug in ast_rewriter.py tracked in python-ast-known-limitations.md item 5. If
        that's ever fixed, callers could go back to one name per call without this batching.
        """
        targets = {names} if isinstance(names, str) else names
        for import_node in self.body:
            raw = cast(ast.AST, import_node.node)
            if not isinstance(raw, ast.ImportFrom) or not any((alias.asname or alias.name) in targets for alias in raw.names):
                continue

            new_import = narrowed_import_text(raw, targets)
            if new_import is not None:
                self.replace(new_import, import_node, False, False)
            else:
                self.remove(import_node)

    def run(self):
        """Perform this recipe's refactoring.

        Overridden by every concrete subclass; the base no-op lets process() call it uniformly
        even for a recipe that hasn't overridden it.
        """
