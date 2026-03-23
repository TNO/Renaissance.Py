from clang import cindex
from renaissance.lst.lst import LSTNode, LST
from typing import Optional
from renaissance.utils.node_util import detect_placeholder


class ClangAdapter:
    def __init__(self, clang_path: Optional[str] = None, args: Optional[list] = None):
        if clang_path:
            cindex.Config.set_library_path(clang_path)
        self.args = args or ["-std=c++17"]

    def parse(self, file_path: str) -> LST:
        index = cindex.Index.create()
        translation_unit = index.parse(file_path, args=self.args)
        return LST(self._convert_node(translation_unit.cursor))

    def load_from_text(self, text: str, file_name: str):
        index = cindex.Index.create()
        translation_unit = index.parse(file_name, unsaved_files=[(file_name, text)], args=[])
        return LST(self._convert_node(translation_unit.cursor))

    def to_lst(self, source_code: str) -> LST:
        # source_code= replace_dollar(source_code)
        return self.load_from_text(source_code, "no_src.cpp")

    def _convert_node(self, cursor: cindex.Cursor, parent: Optional[LSTNode] = None) -> LSTNode:
        try:
            kind = cursor.kind.name
        except Exception as e:
            print(e.__cause__)
            kind = f"invalid kind"
        signature = cursor.spelling or cursor.displayname or kind

        is_ph, coerced_type, ph_name = detect_placeholder(signature, kind)

        node = LSTNode(
            node_type=coerced_type if is_ph else kind,
            properties={
                "spelling": cursor.spelling,
                "type": str(cursor.type.spelling),
                "location": str(cursor.location),
                "is_definition": cursor.is_definition(),
                "name": ph_name,
                **(
                    {
                        "placeholder": True,
                        "placeholder_name": ph_name,
                        "original_node_type": cursor.kind.name,
                    }
                    if is_ph
                    else {}
                ),
            },
            signature=signature,
            offset=cursor.extent.start.offset,
            parent=parent,
        )

        for child in cursor.get_children():
            child_node = self._convert_node(child, parent=node)
            node.add_child(child_node)
        return node
