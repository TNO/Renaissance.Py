
from io import StringIO
import io
from typing import IO
from .ast_node import ASTNode

class ASTShower:
    @staticmethod
    def show_node(ast_node: ASTNode):
        print('\n'+ASTShower.get_node(ast_node))

    @staticmethod
    def get_node(ast_node: ASTNode):
        buffer = io.StringIO()
        ASTShower._process_node(buffer, "", ast_node)
        return buffer.getvalue()

    @staticmethod
    def _process_node( output: StringIO, indent, node: 'ASTNode'):
        if not node.is_part_of_translation_unit():
            return
        
        raw = node.get_raw_signature()
        raw_lines = raw.splitlines()

        output.write(f"{indent}({node.get_kind()}, {node.get_containing_filename()}[{node.get_start_offset()}:{node.get_start_offset()+node.get_length()}]):")
        if len(raw_lines) < 2:
            output.write(f" |{raw}|")
        else:
            for line in raw_lines:
                output.write(f"\n{indent}    |{line}|")
        output.write("\n")

        for child in node.get_children():
            ASTShower._process_node(output, indent + "  ", child)
