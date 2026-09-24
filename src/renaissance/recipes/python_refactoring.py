"""AI: Base processor for Python-specific source refactoring recipes."""

import ast
import importlib
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from termcolor import colored

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.python.ast.util import to_str
from renaissance.syntax_tree import ASTProcessor
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.syntax_tree.semantic_kind import SemanticKind
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
    """AI: Base processor for Python-specific source refactoring recipes."""

    def __init__(self, file):
        """AI: Prepare a Python-specific refactoring processor for the given source file."""
        factory = PythonFactory(PythonRstNode)
        atu = factory.create(file)
        super().__init__(atu, factory, False)
        self.pattern_factory = PythonPatternFactory(self.factory)
        self.black_list_pattern = ".git"
        self.white_list_pattern = ""

    def replace_stmt(self, find, repl):
        """AI: Replace all statements matching the find pattern with the repl template, expanding captures."""
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

    def extract_call_arguments(self, node: PythonRstNode) -> tuple[list[str], dict[str, str]]:
        """Extract positional and keyword arguments from a Call node.

        The input may be a `Call` node itself or any descendant node.
        When given a descendant, this method walks up parent links and uses the first
        ancestor whose semantic kind is `CALL`.

        Returned keyword arguments preserve Python call semantics where keyword
        arguments appear after positional arguments.
        """
        current = node
        while current is not None and current.semantic_kind != SemanticKind.CALL:
            current = current.parent

        call_node = current
        if call_node is None:
            return [], {}

        args_implicit = next((c for c in call_node.children if c.name == "args"), None)
        keywords_implicit = next((c for c in call_node.children if c.name == "keywords"), None)

        positional_args = [arg_node.signature for arg_node in (args_implicit.children if args_implicit else [])]
        keyword_args: dict[str, str] = {}
        for kw_node in keywords_implicit.children if keywords_implicit else []:
            kw_name = kw_node.node.arg
            if kw_name:
                value_node = kw_node.children[0] if kw_node.children else kw_node
                keyword_args[str(kw_name)] = value_node.signature

        return positional_args, keyword_args

    def class_declares_base(self, class_node: PythonRstNode, base_name: str) -> bool:
        """Return whether class_node explicitly declares base_name as a base class.

        This check uses only the names declared in the class header's base list,
        so implicit Python inheritance from `object` is not treated as a declared base.
        """
        return base_name in self.class_base_arguments(class_node)

    def class_base_arguments(self, class_node: PythonRstNode) -> list[str]:
        """Return base class signatures explicitly listed in the class declaration.

        Only names inside the parentheses of ``class Name(...):`` are returned.
        The implicit default base object is not returned when no bases are declared.
        """
        bases_implicit = next((c for c in class_node.children if c.name == "bases"), None)
        if bases_implicit is None:
            return []
        return [child.signature for child in bases_implicit.children]

    @property
    def body(self) -> Sequence[PythonRstNode]:
        """AI: Return the root node's body statements."""
        return cast("PythonRstNode", cast("object", self.root)).body

    def find_rst_node(self, target: ast.AST) -> Any:
        """Locate the PythonRstNode wrapping a raw ast node.

        E.g. after mutating an ast.FunctionDef in place, this finds the RST node to pass to
        self.replace().
        """
        # TODO: Drop once recipes can navigate wrapper nodes via the unified node protocol?
        # 24-09 discussion over future Node Protocol implementation
        found: list[Any] = []

        def visit(node: Any) -> None:
            if node.node is target:
                found.append(node)

        cast("PythonRstNode", cast("object", self.root)).process(visit)
        return found[0]

    def run(self):
        """Perform this recipe's refactoring.

        Overridden by every concrete subclass; the base no-op lets process() call it uniformly
        even for a recipe that hasn't overridden it.
        """
