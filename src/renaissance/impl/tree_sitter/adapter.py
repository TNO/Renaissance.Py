from renaissance.impl.tree_sitter.lst import LST, LSTNode
from renaissance.utils.ast_utils import detect_placeholder, replace_dollar
from tree_sitter import Language, Parser


class TreeSitterAdapter:
    def __init__(self, grammar_module):
        language = Language(grammar_module.language())
        self.language = language
        self.parser = Parser(language)

    def parse_code(self, source_code: str):
        return self.parser.parse(bytes(source_code, "utf8"))

    def to_lst(self, source_code: str, tree) -> LST:
        root_node = tree.root_node
        source_code = replace_dollar(source_code)
        return LST(self._convert_node(root_node, source_code, None))

    def _convert_node(self, node, source_code: str, parent, root=None) -> LSTNode:
        signature = source_code[node.start_byte : node.end_byte]
        is_ph, coerced_type, ph_name = detect_placeholder(signature, node.type)

        lst_node = LSTNode(
            node_type=coerced_type if is_ph else node.type,
            properties={
                "start_point": node.start_point,
                "end_point": node.end_point,
                "source_code": source_code,
                "name": ph_name,
                "is_named": node.is_named,
                **(
                    {
                        "placeholder": True,
                        "placeholder_name": ph_name,
                        "original_node_type": node.type,
                    }
                    if is_ph
                    else {}
                ),
            },
            signature=signature,
            offset=node.start_byte,
            children=[],
            parent=parent,
            root=root,
        )
        if not root:
            root = lst_node

        for child in node.children:
            lst_child = self._convert_node(child, source_code, lst_node, root)
            lst_node.add_child(lst_child)
        return lst_node
