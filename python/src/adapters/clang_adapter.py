from clang import cindex
from lst.lst import LSTNode, LST
from typing import Optional
from utils.placeholders import detect_placeholder


class ClangAdapter:
    def __init__(self, clang_path: Optional[str] = None, args: Optional[list] = None):
        if clang_path:
            cindex.Config.set_library_file(clang_path)
        self.args = args or ["-std=c++17"]

    def parse(self, file_path: str) -> LST:
        index = cindex.Index.create()
        translation_unit = index.parse(file_path, args=self.args)
        return LST(self._convert_node(translation_unit.cursor))

    def load_from_text(self,text: str, file_name: str) -> "ClangASTNode":
        index = cindex.Index.create()
        translation_unit  = index.parse(file_name, unsaved_files=[(file_name, text)], args=[])
        return LST(self._convert_node(translation_unit.cursor))


    def _convert_node(
        self, cursor: cindex.Cursor, parent: Optional[LSTNode] = None
    ) -> LSTNode:
        signature = cursor.spelling or cursor.displayname or cursor.kind.name

        is_ph, coerced_type, ph_name = detect_placeholder(signature, cursor.kind.name)

        node = LSTNode(
            node_type=coerced_type if is_ph else cursor.kind.name,
            properties={
                "spelling": cursor.spelling,
                "type": str(cursor.type.spelling),
                "location": str(cursor.location),
                "is_definition": cursor.is_definition(),
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
        )

        for child in cursor.get_children():
            child_node = self._convert_node(child, parent=node)
            node.add_child(child_node)
        return node
