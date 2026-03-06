from io import StringIO
import io

from .ast_node import ASTNode

IMPLICIT = ['ImplicitNode']
class ASTShower:
    @staticmethod
    def show_node(ast_node: ASTNode, include_properties: bool = False) -> None:
        print("\n" + ASTShower.get_node(ast_node, include_properties))

    @staticmethod
    def show_nodes(ast_nodes: list[ASTNode], include_properties: bool = False) -> None:
        for ast_node in ast_nodes:
            ASTShower.show_node(ast_node, include_properties)

    @staticmethod
    def get_node(ast_node: ASTNode, include_properties: bool = False) -> str:
        buffer = io.StringIO()
        ASTShower._process_node(buffer, "", ast_node, include_properties)
        return buffer.getvalue()

    @staticmethod
    def store_node(filename: str, ast_node: ASTNode, include_properties: bool = False) -> None:
        with open(filename, "w") as f:
            f.write(ASTShower.get_node(ast_node, include_properties))

    @staticmethod
    def _process_node(
            output: StringIO, indent: str, node: ASTNode, include_properties: bool
    ) -> None:
        if node.is_part_of_translation_unit() and node.kind not in IMPLICIT:
            node.indent = indent
            node.show_props =include_properties
            output.write(str(node))
        if node.children:
            for child in node.children:
                ASTShower._process_node(output, indent + "  ", child, include_properties)

