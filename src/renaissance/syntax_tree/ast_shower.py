"""AI: Render an AST node tree to the console for debugging and inspection."""

import io
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Protocol, Self, runtime_checkable

from termcolor import colored

from renaissance.utils.ast_utils import display_context


@runtime_checkable
class Displayable(Protocol):
    """AI: Structural protocol describing the shape required for rendering a node via ASTShower."""

    parser_kind: str
    semantic_kind: object
    children: list[Self]
    is_implicit: bool
    show_props: bool


class ASTShower:
    """AI: Render an AST node tree to the console for debugging and inspection."""

    focus: str = "NO-FOCUS-DEFINED"

    @staticmethod
    def show_node(node, include_properties: bool = False, display_parser_kind: bool = False) -> None:
        """AI: Print node's rendered tree to the console."""
        print("\n" + ASTShower.get_node(node, include_properties, display_parser_kind))

    @staticmethod
    def show_nodes(ast_nodes: Sequence, include_properties: bool = False, display_parser_kind: bool = False) -> None:
        """AI: Print each node's rendered tree to the console."""
        for ast_node in ast_nodes:
            ASTShower.show_node(ast_node, include_properties, display_parser_kind)

    @staticmethod
    def get_node(ast_node: Displayable, include_properties: bool = False, display_parser_kind: bool = False) -> str:
        """AI: Return the rendered tree text for ast_node, or an empty string if it is not Displayable."""
        if isinstance(ast_node, Displayable):
            buffer = io.StringIO()
            with display_context(display_parser_kind):
                ASTShower._process_node(buffer, "", ast_node, include_properties)
            return buffer.getvalue()
        return ""

    @staticmethod
    def store_node(filename: str, ast_node: Displayable, include_properties: bool = False, display_parser_kind: bool = False) -> None:
        """AI: Write ast_node's rendered tree text to the file named filename."""
        with Path(filename).open("w") as f:
            f.write(ASTShower.get_node(ast_node, include_properties, display_parser_kind))

    @staticmethod
    def _process_node(output: StringIO, indent: str, node: Displayable, include_properties: bool) -> None:
        if node.is_implicit:
            node.indent = indent
            node.show_props = include_properties
            raw = str(node)
            raw = raw.replace(ASTShower.focus, colored(ASTShower.focus, "red", attrs=["bold"]))
            output.write(raw)
        if node.children:
            for child in node.children:
                ASTShower._process_node(output, indent + "  ", child, include_properties)
