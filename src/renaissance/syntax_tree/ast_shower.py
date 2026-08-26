import io
from collections.abc import Sequence
from io import StringIO
from typing import Protocol, Self, runtime_checkable

from termcolor import colored


@runtime_checkable
class Displayable(Protocol):
    ast_type: str
    children: list[Self]
    is_implicit: bool
    show_props: bool


class ASTShower:
    focus: str = "NO-FOCUS-DEFINED"

    @staticmethod
    def show_node(node, include_properties: bool = False) -> None:
        print("\n" + ASTShower.get_node(node, include_properties))

    @staticmethod
    def show_nodes(ast_nodes: Sequence, include_properties: bool = False) -> None:
        for ast_node in ast_nodes:
            ASTShower.show_node(ast_node, include_properties)

    @staticmethod
    def get_node(ast_node: Displayable, include_properties: bool = False) -> str:
        if isinstance(ast_node, Displayable):
            buffer = io.StringIO()
            ASTShower._process_node(buffer, "", ast_node, include_properties)
            return buffer.getvalue()
        return ""

    @staticmethod
    def store_node(filename: str, ast_node: Displayable, include_properties: bool = False) -> None:
        with open(filename, "w") as f:
            f.write(ASTShower.get_node(ast_node, include_properties))

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
