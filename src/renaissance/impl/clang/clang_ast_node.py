import sys
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Any, override

import clang.native
from clang.cindex import Config, CursorKind, Index, TypeKind
from clang.cindex import TranslationUnit as ClangCindexTranslationUnit

from renaissance.impl.clang.cpp_utils import matches_kind
from renaissance.impl.types import (
    KIND_MAP,
    BinaryOperation,
    CompoundStatement,
    Declaration,
    DeclarationExpression,
    Definition,
    Literal,
    MacroDef,
    MatchAll,
    MatchOne,
    Statement,
    TranslationUnit,
    UnaryOperation,
    UnknownType,
)
from renaissance.syntax_tree import ASTFinder, ASTNode, ASTReference
from renaissance.utils.ast_utils import match_children, match_props

EMPTY_DICT = {}
EMPTY_STR = ""
EMPTY_LIST = []

STMT_PARENTS = [CompoundStatement, TranslationUnit]
IRRELEVANT_PROPS = {"comment"}
IRRELEVANT_NODES = {"comment"}
PRINT_ALL_NODES = False


class Clangastreference:
    def __init__(self, node_id: str, ref_kind: str, properties: dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class ClangTranslationUnit:
    cache = []

    def __init__(self, clang_atu: ClangCindexTranslationUnit, file_name: str):
        self.clang_atu = clang_atu
        self.file_name = file_name
        self.references_initialized = False
        # print_node_kind(clang_atu.cursor)
        self.macro_expansions = ClangTranslationUnit._collect_expansions(clang_atu)
        # references are used as a cache to store the references of a node
        # they are stored as id for lazy creation
        self._references: dict[str, list[Clangastreference]] = {}
        self._referenced_by: dict[str, list[Clangastreference]] = {}
        self._nodes: dict[str, ClangASTNode] = {}

    def lazy_create_references(self, node: ClangASTNode) -> None:
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        self.references_initialized = True

    @staticmethod
    def _collect_expansions(
        translation_unit: ClangCindexTranslationUnit,
    ) -> set[tuple[str, int, int]]:
        result: set[tuple[str, int, int]] = set()
        for child in translation_unit.cursor.get_children():
            if child.kind.name == "MACRO_INSTANTIATION":
                result.add(
                    (
                        child.extent.start.file,
                        child.extent.start.offset,
                        child.extent.end.offset,
                    ),
                )
        return result


class ClangASTNode(ASTNode):
    @staticmethod
    def set_library_path() -> None:
        try:
            Config.set_library_path(Path(clang.native.__file__).parent)
        except Exception as e:
            print(e)

    set_library_path()
    index = Index.create()
    parse_args = [
        "-fparse-all-comments",
        "-ferror-limit=0",
        "-Xclang",
        "-detailed-preprocessing-record",
        "-fsyntax-only",
    ]

    def __init__(
        self,
        node,
        translation_unit: ClangTranslationUnit,
        parent=None,
        start_offset: int | None = None,
        length: int | None = None,
        insert_kind: str | None = None,
    ):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children = None
        self._parent = parent
        self.translation_unit = translation_unit
        self.inserted = insert_kind is not None
        self.show_props = False
        self._filename = self._get_containing_filename()
        self._name = self._derive_name()
        # if the node has not been added to the translation unit, add it
        # a node might already be added if it is split into multiple nodes
        # an example is for base types like int, char, etc. which are split into multiple nodes
        if self.node.hash not in self.translation_unit._nodes:
            self.translation_unit._nodes[node.hash] = self
        self._offset = start_offset if start_offset is not None else self.__derive_start_offset()
        self._length = length if length is not None else self.__derive_length()
        self._kind = insert_kind if insert_kind is not None else self.__derive_kind()
        self.ast_type = KIND_MAP.get(self._kind, UnknownType)
        self.indent = ""
        # TODO: TextUtils.get_indent(self.content, self._offset)
        # an fake child is introduced to handle the case where the type of a declaration is not found
        # for example in the case of a base type.
        # without the fake child pattern matching on types will be difficult
        self.__inserted_children = []
        # NOTE: clang.cindex.{TypeKind,CursorKind} assign their named members via
        # runtime attribute assignment after the class body (e.g. `TypeKind.INVALID =
        # TypeKind(0)`), so pyright cannot see them as declared class attributes from
        # this module, hence the `pyright: ignore[reportAttributeAccessIssue]` below.
        if (
            insert_kind is None
            and not self.node.location.is_in_system_header
            and self.node.kind.is_declaration()
            and self.node.type.kind != TypeKind.INVALID  # pyright: ignore[reportAttributeAccessIssue]
        ):
            loc_offset: int = self.node.location.offset
            length = len(self.node.spelling.encode(sys.getdefaultencoding()))
            insert_child = ClangASTNode(self.node, self.translation_unit, self, loc_offset, length, "DECL_LOC")
            insert_child._children = []
            self.__inserted_children.append(insert_child)
            if self.node.type.get_declaration().kind is CursorKind.NO_DECL_FOUND:  # pyright: ignore[reportAttributeAccessIssue]
                my_type = (
                    self.node.type
                    if self.node.result_type.kind == TypeKind.INVALID  # pyright: ignore[reportAttributeAccessIssue]
                    else self.node.result_type
                )
                length_ref = len(my_type.spelling.encode(sys.getdefaultencoding()))
                insert_child = ClangASTNode(
                    self.node,
                    self.translation_unit,
                    self,
                    self._offset,
                    length_ref,
                    CursorKind.TYPE_REF.name,  # pyright: ignore[reportAttributeAccessIssue]
                )
                insert_child._children = []
                self.__inserted_children.append(insert_child)

        self._children = []
        for n in self.__inserted_children:
            self._children.append(n)
        for n in self.node.get_children():
            if not is_system_macro(n) and n.kind.name != "MACRO_INSTANTIATION":
                self._children.append(ClangASTNode(ClangASTNode.remove_wrapper(n), self.translation_unit, self))

        self._properties = self._derive_properties()
        if self.ast_type == DeclarationExpression:
            self._properties["name"] = self._name

    def __eq__(self, other):
        return (
            other
            and isinstance(other, type(self))
            and self.ast_type == other.ast_type
            and match_props(self.properties, other.properties, IRRELEVANT_PROPS)
            and match_children(self.children, other.children, IRRELEVANT_NODES)
        )

    def __hash__(self):
        return hash((self.ast_type, frozenset(self.properties.items())))

    @override
    @staticmethod
    def load(file_path: Path, extra_args: Sequence[str], working_dir: Path) -> ClangASTNode:
        args = [*extra_args, *ClangASTNode.parse_args]
        translation_unit: ClangCindexTranslationUnit = ClangASTNode.index.parse(working_dir / file_path, args=args[3:])
        ClangASTNode.check_diagnostics(translation_unit, file_path.name)
        root_node = ClangASTNode(
            translation_unit.cursor,
            ClangTranslationUnit(translation_unit, file_name=str(file_path)),
            None,
        )
        return root_node

    @override
    @staticmethod
    def load_from_text(
        text: str,
        file_name: str,
        extra_args: Sequence[str] = None,
        working_dir: Path = None,
    ) -> ClangASTNode:
        # Convert file_content to bytes
        file_content_bytes = text.encode(sys.getfilesystemencoding())
        # add to cache to avoid reading the file again
        ASTNode.cache[file_name] = file_content_bytes
        args = [*ClangASTNode.parse_args, *extra_args] if extra_args is not None else [*ClangASTNode.parse_args]
        translation_unit: ClangCindexTranslationUnit = ClangASTNode.index.parse(file_name, unsaved_files=[(file_name, text)], args=args)
        ClangASTNode.check_diagnostics(translation_unit, file_name)
        try:
            root_node = ClangASTNode(
                translation_unit.cursor,
                ClangTranslationUnit(translation_unit, file_name=str(file_name)),
                None,
            )
        except Exception as e:
            print(e)
            raise e
        ClangASTNode.check_diagnostics(translation_unit, file_name)
        return root_node

    @staticmethod
    def check_diagnostics(translation_unit: ClangCindexTranslationUnit, file_name: str) -> None:
        has_error = False
        errors = ""
        for d in translation_unit.diagnostics:
            if d.severity >= 3:
                has_error = True
                errors += f"{d.severity}: {d.spelling} at {d.location}\n"
            print(f"{d.severity}: {d.spelling} at {d.location}")
        if has_error:
            raise Exception(f"Error parsing: {file_name} \n+ errors: {errors}")

    def _derive_name(self) -> str:
        try:
            # NOTE: see the clang.cindex enum note near __init__ above.
            if self.node.type.kind == TypeKind.RECORD:  # pyright: ignore[reportAttributeAccessIssue]
                return self.node.type.spelling
        except Exception as e:
            print(e)
        try:
            return self.node.spelling
        except Exception as e:
            print(e)
        return EMPTY_STR

    def _get_containing_filename(self) -> str:
        if self is self.root:
            return self.translation_unit.clang_atu.spelling
        try:
            return self.node.location.file.name
        except Exception:
            return EMPTY_STR

    @override
    @property
    def extended_end_offset(self) -> int:
        try:
            end_offset = self._offset + self._length
            if (
                (not self._is_statement_or_declaration())
                and (self.parent and self.parent.ast_type in STMT_PARENTS)
                and self.ast_type not in [MacroDef]
            ):
                content = self.root.binary_file_content()
                while end_offset < len(content) and content[end_offset - 1] not in b";":
                    end_offset += 1
            return end_offset
        except Exception:
            return 0

    def _is_statement_or_declaration(self):
        print(f"{self.ast_type} is statement: {self.kind}")
        return isinstance(self.ast_type(), (Statement, Declaration, Definition))

    @override
    def matches_kind(self, node: ASTNode) -> bool:
        return matches_kind(self.ast_type, node.ast_type)

    def _derive_properties(self) -> dict[str, int | str]:
        result = {}
        offsets = (self.filename, self.offset, self.end_offset)
        if offsets in self.translation_unit.macro_expansions:
            result["macro_expansion"] = self.text

        if self.ast_type == BinaryOperation:
            # TODO remove below code after clang release that supports the getOpCode() statement
            children = self.children
            start_offset = children[0].offset + children[0].length
            end_offset = children[1].offset
            operator = self.content(start_offset, end_offset)
            result["operator"] = operator.strip()
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif self.ast_type == UnaryOperation:
            # TODO remove below code after clang release that supports the getOpCode() statement
            child = self.children[0]
            # list all attributes of self.node excluding the once starting with _

            if child.offset > self.offset:
                start_offset = self.offset
                end_offset = child.offset
                prefix_operator = True
            else:
                start_offset = child.offset + child.length
                end_offset = self.offset + self.length
                prefix_operator = False

            operator = self.content(start_offset, end_offset)
            result["operator"] = operator.strip()
            result["prefixOperator"] = prefix_operator
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif isinstance(self.ast_type(), Literal) or self.ast_type == DeclarationExpression:
            self._add_tokens(result, "LITERAL")

        is_all = {
            attr[len("is_") :]: True
            for attr in dir(self.node)
            if attr.startswith("is_") and callable(getattr(self.node, attr)) and getattr(self.node, attr)()
        }
        result.update(is_all)
        return result

    @override
    @property
    def is_statement(self) -> bool:
        """Pretty good definition."""
        return self.parent is not None and self.parent.ast_type in STMT_PARENTS

    @override
    @property
    def referenced_by(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_references(self)
        node_id = self.node.hash
        ref_by = self.translation_unit._referenced_by.get(node_id, EMPTY_LIST)
        # if both the function declaration and function definition are available
        # the references are stored in the function definition,
        # but we want them to also show up in the declaration
        if len(ref_by) == 0:
            definition = self._get_function_definition()
            if definition:
                ref_by = self.translation_unit._referenced_by.get(definition.node.hash, EMPTY_LIST)
        return list(
            ASTReference(
                self.translation_unit._nodes[ref.node_id],
                ref.ref_kind,
                ref.properties,
            )
            for ref in ref_by
        )

    def _get_function_definition(self):
        # NOTE: see the clang.cindex enum note near __init__ above.
        if self.node.type.kind == TypeKind.FUNCTIONPROTO:  # pyright: ignore[reportAttributeAccessIssue]
            signature = self.node.displayname
            semantic_parent = self.node.semantic_parent.hash

            def has_body(node):
                return any(
                    c.kind == CursorKind.COMPOUND_STMT  # pyright: ignore[reportAttributeAccessIssue]
                    for c in node.node.get_children()
                )

            def is_match(node):
                if node._kind != self._kind:
                    return False
                if node.node.type.kind != TypeKind.FUNCTIONPROTO:  # pyright: ignore[reportAttributeAccessIssue]
                    return False
                if node.node.semantic_parent.hash != semantic_parent:
                    return False
                if node.node.displayname != signature:
                    return False
                return has_body(node)

            if has_body(self):
                return None
            body = ASTFinder.find_all(self.root, is_match).find_first().or_else(None)  # type: ignore
            if isinstance(body, ClangASTNode):
                return body
        return None

    @override
    @property
    def references(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_references(self)
        return list(
            ASTReference(
                self.translation_unit._nodes[ref.node_id],
                ref.ref_kind,
                ref.properties,
            )
            for ref in self.translation_unit._references.get(self.node.hash, EMPTY_LIST)
        )

    def _add_tokens(self, result: dict[str, str], *token_kind):
        for token in self.node.get_tokens():
            # find all attr of token that are of type str or int
            kind = str(token.kind).split(".")[-1]
            if kind in token_kind:
                result[kind] = token.spelling

    def __derive_start_offset(self) -> int:
        try:
            if self.node.kind.name == "MACRO_DEFINITION":
                return self.node.extent.start.offset - 8

            return self.node.extent.start.offset

        except Exception:
            return 0

    def __derive_length(self) -> int:
        try:
            if self.node.kind.name in ["VAR_DECL", "STRUCT_DECL"]:
                end_offset = self.node.extent.end.offset + 1
            elif self.node.kind.name in ["MACRO_DEFINITION"]:
                end_offset = self.node.extent.end.offset
            else:
                end_offset = self.node.extent.end.offset
            return end_offset - self.__derive_start_offset()
        except Exception:
            return 0

    def __derive_kind(self) -> str:
        try:
            if self.node.kind.name == "MACRO_DEFINITION":
                return str(self.node.kind.name)
            if self.node.kind.name in ["UNEXPOSED_EXPR", "VAR_DECL", "DECL_REF_EXPR"]:
                if self.node.displayname.startswith("$$") and " " not in self.node.displayname:
                    return MatchAll.__name__
                if self.node.displayname.startswith("$") and " " not in self.node.displayname:
                    return MatchOne.__name__
            return str(self.node.kind.name)
        except Exception:
            return EMPTY_STR

    @staticmethod
    def remove_wrapper(cursor):
        try:
            if ClangASTNode._is_wrapped(cursor):
                return ClangASTNode.remove_wrapper(list(cursor.children)[0])
        except Exception:
            pass
        return cursor

    @staticmethod
    def _is_reference(node):
        # refactor this
        try:
            print(type(node))
            print(vars(node))
            print(dir(node))
            print(node.__dict__)
            node.__dict__["id"]
            return True
        except Exception:
            return False

    @staticmethod
    @cache
    def __is_property(key, value):
        return callable(value) and any(key.startswith(tag) for tag in ["is_", "get"])

    @staticmethod
    def _is_wrapped(cursor):
        return cursor.kind.is_unexposed() and len(list(cursor.children)) == 1

    @property
    def is_implicit(self):
        return self.is_part_of_translation_unit()


#    def get_ancestor(self, types ):
#        return get_ancestor(self, types)


SYSTEM_MACROS = {
    "linux",
    "unix",
    "_LP64",
    "_WIN32",
    "_WIN64",
    "_ISO_VOLATILE",
    "_INTEGRAL_MAX_BITS",
}


def is_system_macro(n):
    return n.kind.name == "MACRO_DEFINITION" and (
        n.displayname.startswith("__")
        or n.displayname.startswith("_MS")
        or n.displayname.startswith("_M_")
        or n.displayname in SYSTEM_MACROS
    )


class ReferenceHelper:
    @staticmethod
    def create_references(ast_node: ClangASTNode) -> None:
        assert isinstance(ast_node, ClangASTNode), f"Expected ClangASTNode but got {type(ast_node)}"
        references = []
        node_id: str = ast_node.node.hash
        ast_node.translation_unit._references[node_id] = references
        ref_fields = ["referenced"]  # , 'type.get_declaration()']
        for field in ref_fields:
            try:
                element = eval("ast_node.node." + field)
                if element.kind.name == "NO_DECL_FOUND":
                    continue
                ref_id = element.hash
                ref_kind = field.split(".")[0]
                properties = {k: p for k, p in element.__dict__.items() if not k.startswith("_") and k != "hash"}
                if node_id == ref_id:
                    return
                reference = Clangastreference(ref_id, ref_kind, properties)
                referenced_by = Clangastreference(
                    node_id,
                    ref_kind,
                    {k: p for k, p in ast_node.node.__dict__.items() if k != "hash"},
                )
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except Exception:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                references.append(reference)
            except Exception:
                pass
