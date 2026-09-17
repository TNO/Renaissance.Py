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
from renaissance.syntax_tree.semantic_kind import SemanticKind
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

    def extract_call_arguments(self, node: PythonRstNode) -> tuple[list[str], dict[str, str]]:
        """
        Extract positional and keyword arguments from a Call node.

        The input can be either a `Call` node itself or a node directly contained in a call.
        Returned keyword arguments preserve Python call semantics where keyword arguments
        appear after positional arguments.
        """
        call_node = node if node is not None and node.semantic_kind == SemanticKind.CALL else getattr(node, "parent", None)
        if call_node is None or call_node.semantic_kind != SemanticKind.CALL:
            return [], {}

        args_implicit = next((c for c in call_node.children if getattr(c, "name", None) == "args"), None)
        keywords_implicit = next((c for c in call_node.children if getattr(c, "name", None) == "keywords"), None)

        positional_args = [arg_node.signature for arg_node in (args_implicit.children if args_implicit else [])]
        keyword_args: dict[str, str] = {}
        for kw_node in (keywords_implicit.children if keywords_implicit else []):
            kw_name = kw_node.properties.get("arg")
            if kw_name:
                value_node = kw_node.children[0] if kw_node.children else kw_node
                keyword_args[str(kw_name)] = value_node.signature

        return positional_args, keyword_args

    def class_inherits_from(self, class_node: PythonRstNode, base_name: str) -> bool:
        return base_name in self.class_base_arguments(class_node)

    def class_base_arguments(self, class_node: PythonRstNode) -> list[str]:
        bases_implicit = next((c for c in class_node.children if getattr(c, "name", None) == "bases"), None)
        if bases_implicit is None:
            return []
        return [child.signature for child in bases_implicit.children]

    @property
    def body(self) -> Sequence[PythonRstNode]:
        return cast("PythonRstNode", cast("object", self.root)).body

    def run(self):
        pass
