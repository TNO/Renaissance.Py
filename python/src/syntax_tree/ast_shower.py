
from io import StringIO
import io
from .ast_node import ASTNode

class ASTShower:
    @staticmethod
    def show_node(ast_node: ASTNode, include_properties = False):
        print('\n'+ASTShower.get_node(ast_node, include_properties))

    @staticmethod
    def get_node(ast_node: ASTNode, include_properties = False):
        buffer = io.StringIO()
        ASTShower._process_node(buffer, "", ast_node, include_properties)
        return buffer.getvalue()

    @staticmethod
    def _process_node( output: StringIO, indent, node: ASTNode, include_properties):
        if not node.is_part_of_translation_unit():
            return
        
        text = node.get_text()
        raw_lines = text.splitlines()
        properties_text = node.get_properties() if include_properties else ""
        output.write(f"{indent}({node.get_kind()}, {node.get_name()}, {node.get_containing_filename()}[{node.get_start_offset()}:{node.get_start_offset()+node.get_length()}]){properties_text}:")
        if len(raw_lines) < 2:
            output.write(f" |{text}|")
        else:
            for line in raw_lines:
                output.write(f"\n{indent}    |{line}|")
        output.write("\n")

        for child in node.get_children():
            ASTShower._process_node(output, indent + "  ", child, include_properties)
