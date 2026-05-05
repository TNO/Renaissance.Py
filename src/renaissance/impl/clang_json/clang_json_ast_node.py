# create a class that inherits syntax tree ASTNode

from __future__ import annotations
from functools import cache
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Optional, Sequence
from typing_extensions import override
import subprocess

from renaissance.impl.types import MatchAll, MatchOne
from renaissance.syntax_tree import ASTNode, CPPUtils, ASTReference
from renaissance.utils.ast_utils import match_children, match_props

EMPTY_DICT = {}
EMPTY_STR = ""
EMPTY_LIST: list[ClangJsonASTReference] = []
ON_NODE_ID_TAGS = ["previousDecl", "parentDeclContextId"]
ID_TAGS = [
    "id",
    "typeAliasDeclId",
    "templateDeclId",
    "templateSpecializationDeclId",
    "referencedDeclId",
    *ON_NODE_ID_TAGS,
]

STMT_PARENTS = ["CompoundStmt", "TranslationUnitDecl"]
IRRELEVANT_PROPS = {"macro_expansion", "start_point", "end_point", "source_code", "location", "type"}
IRRELEVANT_NODES = {"COMMENT", "FullComment", "MACRO_DEFINITION", "Comment"}
VERBOSE = False


class ClangJsonASTReference:
    def __init__(self, node_id: str, ref_kind: str, properties: dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class ClangJsonTranslationUnit:
    def __init__(self, json_root: dict[str, Any], file_name: str):
        self.json_root = json_root
        self.filename = file_name
        self.references_initialized = False
        # references are used as a cache to store the references of a node
        # the are stored as id for lazy creation
        self._references: dict[str, list[ClangJsonASTReference]] = {}
        self._referenced_by: dict[str, list[ClangJsonASTReference]] = {}
        self._nodes: dict[str, ClangJsonASTNode] = {}

    def lazy_create_references(self, node: ClangJsonASTNode) -> None:
        # TODO: Do I correctly assume that the usage of this function must be synchronized?
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        node.root.process(ReferenceHelper.add_record_references)
        self.references_initialized = True


class ClangJsonASTNode(ASTNode):
    parse_args = [
        "-fparse-all-comments",
        "-ferror-limit=0",
        "-Xclang",
        "-ast-dump=json",
        "-fsyntax-only",
    ]

    def __init__(
        self,
        node: dict[str, Any],
        translation_unit: ClangJsonTranslationUnit,
        parent: Optional[ClangJsonASTNode] = None,
        start_offset: Optional[int] = None,
        length: Optional[int] = None,
        insert_kind: Optional[str] = None,
        insert_name: Optional[str] = None,
    ) -> None:
        super().__init__(self if parent is None else parent.root)
        self.node: dict[str, Any] = node
        self._children: Optional[Sequence[ClangJsonASTNode]] = None
        self._parent = parent
        self.translation_unit = translation_unit
        self._filename = translation_unit.filename
        self.inserted = insert_kind is not None
        self.show_props = False
        # if the node has not been added to the translation unit, add it
        # a node might already be added if it is split into multiple nodes
        # an example is for base types like int, char, etc. which are split into multiple nodes
        if "id" in node and self.translation_unit._nodes.get(node["id"]) == None:
            self.translation_unit._nodes[node["id"]] = self
        self._offset = start_offset if start_offset is not None else self.__derive_start_offset()
        self._end_offset = self._offset + length if length != None else self.__derive_end_offset()
        self._length = self._end_offset - self._offset
        self._kind = insert_kind if insert_kind is not None else self.__derive_kind()
        self._name = insert_name if insert_name is not None else self._derive_name()
        # an fake child is introduced to handle the case where the type of a declaration is not found
        # for example in the case of a base type.
        # without the fake child pattern matching on types will be difficult
        self.__inserted_children: list[ClangJsonASTNode] = []
        type = self.node.get("type")
        if insert_kind == None and type and not self.node.get("implicit") and re.fullmatch("(Var|Function|CxxMethod)Decl", self._kind):
            declared_type = type["qualType"].replace("(", "").replace(")", "").strip()
            if self.node.get("loc"):
                loc = self.node["loc"]
                offset = loc["offset"] if loc.get("offset") else self._get(["loc", "expansionLoc", "offset"], 0)
                tokLen = loc["tokLen"] if loc.get("tokLen") else self._get(["loc", "expansionLoc", "tokLen"], 0)
                if tokLen != 0:
                    insert_child = ClangJsonASTNode(
                        self.node,
                        self.translation_unit,
                        self,
                        offset,
                        tokLen,
                        "DeclLoc",
                    )
                    insert_child._children = []
                    self.__inserted_children.append(insert_child)
            if not "TypeRef" in [inner["kind"] for inner in self.node.get("inner", [])]:
                # deep clone the type node and remove the parentheses
                base_type = type.get("desugaredQualType", declared_type).replace("(", "").replace(")", "").strip()
                if base_type in CPPUtils.RESERVED_KEYWORDS:
                    length_ref = len(declared_type.encode(sys.getdefaultencoding()))
                    insert_child = ClangJsonASTNode(
                        self.node,
                        self.translation_unit,
                        self,
                        self._offset,
                        length_ref,
                        "TypeRef",
                        declared_type,
                    )
                    insert_child._children = []
                    self.__inserted_children.append(insert_child)
            # add the declaration as node
            # deep clone the type node and remove the parentheses
        elif self._kind in ["DeclRefExpr"]:
            if self.name.startswith("$$"):
                self._kind = MatchAll.__name__
            elif self.name.startswith("$"):
                self._kind = MatchOne.__name__

        self._children = self.__inserted_children + [
            ClangJsonASTNode(
                ClangJsonASTNode._remove_wrapper(n),
                translation_unit=self.translation_unit,
                parent=self,
            )
            for n in self.node.get("inner", [])
            if not n.get("isImplicit", False)
        ]
        self._children = [n for n in self._children if n.kind not in IRRELEVANT_NODES]

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.kind == other.kind
            and match_props(self.properties, other.properties, IRRELEVANT_PROPS)
            and match_children(self.children, other.children, IRRELEVANT_NODES)
        )

    @override
    @staticmethod
    def load(
        file_path: Path,
        extra_args: Sequence[str],
        working_dir: Path,
        code: Optional[str] = None,
    ) -> ClangJsonASTNode:
        # in a shell process compile the file_path with clang compiler
        try:
            # remove the compiler name if it is the first argument
            if len(extra_args) > 0 and re.match(r".*(g\+\+|gcc|cl\.exe).*", extra_args[0]):
                extra_args = extra_args[1:]
            # add clang compiler if it is not in the arguments
            if len(extra_args) == 0 or not "clang" in extra_args[0]:
                clang = "clang++" if file_path.suffix == ".cpp" else "clang"
                extra_args = [clang, *extra_args]

            command = [*extra_args, *ClangJsonASTNode.parse_args]
            if code:
                if str(file_path) in command:
                    command.remove(str(file_path))
                compile = "-xc++" if file_path.suffix == ".cpp" else "-xc"
                if not compile in command:
                    command.append(compile)
                if not "-" in command:
                    command.append("-")
                # command.append('-main-file-name=' + str(file_path))
                input = code
                result = subprocess.run(
                    command,
                    input=input,
                    capture_output=True,
                    text=True,
                    cwd=working_dir,
                )
                length = len(input)
            else:
                if str(file_path) not in command:
                    command.append(str(file_path))
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=working_dir,
                )
                length = os.path.getsize(working_dir / file_path)
            json_dump = result.stdout.replace("<stdin>", str(file_path))
            error = result.stderr

            if VERBOSE:
                temp_dir = tempfile.gettempdir()
                temp_file_name = os.path.join(temp_dir, file_path.name + ".ast.json")
                with open(temp_file_name, "w") as std_out_file:
                    print("result stored in " + temp_file_name)
                    std_out_file.write(json_dump)
            print(error, file=sys.stderr)
            json_atu = json.loads(json_dump)
            atu = ClangJsonASTNode(
                json_atu,
                translation_unit=ClangJsonTranslationUnit(json_atu, file_name=str(file_path)),
                length=length,
            )
            if code:
                atu.cache[str(file_path)] = code.encode(sys.getfilesystemencoding())
            else:
                with open(working_dir / file_path, "rb") as f:
                    atu.cache[str(file_path)] = f.read()
            # cache the result of the temp file before deleting it
            atu.content(0, 0)
            return atu

        except Exception as e:
            print("Call to clang failed. Did you install clang?, is it on the env path?")
            raise e

    @override
    @staticmethod
    def load_from_text(text: str, file_name: str, extra_args: Sequence[str], working_dir: Path) -> ClangJsonASTNode:
        return ClangJsonASTNode.load(Path(file_name), extra_args, working_dir, code=text)

    @cache
    def _get_containing_filename(self) -> str:
        if self.node.get("isImplicit", False):
            return ""
        if self.node.get("implicit", False):
            return ""
        if not self.parent:
            return self.translation_unit.file_name
        # return the file name of the node if it exists else return the file name of the parent node
        containing_file = self._get(["loc", "file"], EMPTY_STR)
        if containing_file:
            return containing_file
        included_file = self._get(["loc", "includedFrom", "file"], "")
        if included_file:  # included but no file location is provided in the node so we don't know the file name
            return ""
        included_file = self._get(["loc", "spellingLoc", "includedFrom", "file"], "")
        if included_file:  # included but no file location is provided in the node so we don't know the file name
            return ""
        # not included and no file location so it is the same as the parent
        if self.parent:
            return self.parent.filename
        return EMPTY_STR

    @override
    @property
    def extended_end_offset(self) -> int:
        try:
            endOffset = self._end_offset
            # TODO: Do I correctly assume this is for Expression Statements like
            # "f(x,y);" and "a = f(3);" that are according to clang NOT statements,
            # but expressions (without the semicolon)
            if (not self._is_statement_or_declaration()) and (self.parent and self.parent.kind in STMT_PARENTS):
                content = self.root.binary_file_content()
                while endOffset < len(content) and not content[endOffset - 1] in b";":  # Why use 'in' when list has one element, i.e. ';'?
                    endOffset += 1
            return endOffset
        except:
            return 0

    def _is_statement_or_declaration(self):
        return re.match("(?i).*(Stmt|Decl)", self.kind)

    @override
    @property
    def matches_kind(self, node: ASTNode) -> bool:
        self_kind = self._kind
        node_kind = node.kind
        return (
            self_kind == node_kind
            or (self_kind.endswith("Literal") and node_kind == "DeclRefExpr")
            or (self_kind == "DeclRefExpr" and node_kind.endswith("Literal"))
        )

    @override
    @property
    def properties(self) -> dict[str, Any]:
        # get all the attributes of self.node except the inner  nodes, id, location, range, kind and name and all reference nodes (that is children with 'id)
        properties = {
            k: ClangJsonASTNode._remove_ids(v)
            for k, v in self.node.items()
            if ClangJsonASTNode.__is_property(k) and not ClangJsonASTNode._is_reference(v) == None
        }
        if self._get(["range", "end", "expansionLoc", "offset"], -1) != -1:  # dealing with a macro expansion
            properties["macro_expansion"] = self.text
        # matching name through props
        if self.kind == "DeclRefExpr":
            properties["name"] = self.name

        return properties

    @override
    @property
    def referenced_by(self) -> Sequence[ASTReference]:
        if self.inserted:
            return []
        self.translation_unit.lazy_create_references(self)
        ref_by = self.translation_unit._referenced_by.get(self.node["id"], EMPTY_LIST)
        definition_node_id = self._get_function_definition()
        if definition_node_id:
            # try to find the definition which might have references
            ref_by += self.translation_unit._referenced_by.get(definition_node_id, EMPTY_LIST)
        return [
            ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)
            for ref in ref_by
            if ref.node_id != self.node["id"]
        ]

    def _get_function_definition(self):
        refs = self.translation_unit._referenced_by.get(self.node["id"], EMPTY_LIST)
        for ref in refs:
            if ref.ref_kind == "previousDecl":
                return ref.node_id
        return None

    @override
    @property
    def references(self) -> list[ASTReference]:
        if self.inserted:
            return []
        self.translation_unit.lazy_create_references(self)

        refs = self.translation_unit._references.get(self.node["id"], EMPTY_LIST)
        definition_node_id = self._get_function_definition()
        # TODO: also class definitions, type definitions, ...
        if definition_node_id:
            # try to find the definition which might have references
            refs += self.translation_unit._references.get(definition_node_id, EMPTY_LIST)
        # remove duplicates
        refs = list({ref.node_id: ref for ref in refs}.values())

        return [
            ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)
            for ref in refs
            if ref.node_id != self.node["id"]
        ]

    @override
    @property
    def is_statement(self) -> bool:
        return (
            self.parent != None and self.parent.kind in STMT_PARENTS
        )  # TODO: Why look at the kind of your parent and not at your own kind?

    def _derive_name(self) -> str:
        name = self.node.get("name")
        if name:
            return name
        kind = self.node.get("kind")
        decl_ref_name_path = ["referencedDecl", "name"]
        if kind == "CallExpr":
            # equalize with libclang
            decl_ref_child = [inner["kind"] for inner in self.node.get("inner", []) if inner.get("kind") == "DeclRefExpr"]
            if decl_ref_child:
                return self._get_property(decl_ref_child[0], decl_ref_name_path, default=EMPTY_STR)
        if kind == "DeclRefExpr":
            return self._get(decl_ref_name_path, default=EMPTY_STR)
        if kind == "StringLiteral":
            return self._get(["value"], default=EMPTY_STR)
        return self.node.get("name", EMPTY_STR)

    def __derive_start_offset(self) -> int:
        offset = self._get(["range", "begin", "offset"], default=-1)
        if offset == -1:
            # we might be dealing with a macro in that case use the expansion location
            offset = self._get(["range", "begin", "expansionLoc", "offset"], default=0)
        return offset

    def __derive_end_offset(self) -> int:
        if self.__derive_kind() == "TranslationUnitDecl":
            return len(self.binary_file_content(self.filename))
        offset = self._get(["range", "end", "offset"], default=-1)
        tokLen = self._get(["range", "end", "tokLen"], default=-1)
        if offset == -1:
            # we might be dealing with a macro in that case use the expansion location
            offset = self._get(["range", "end", "expansionLoc", "offset"], default=0)
            tokLen = self._get(["range", "end", "expansionLoc", "tokLen"], default=0)

        return offset + tokLen

    def __derive_kind(self) -> str:
        return self.node.get("kind", EMPTY_STR)

    @staticmethod
    def _remove_wrapper(node):
        try:
            if ClangJsonASTNode._is_wrapped(node):
                return ClangJsonASTNode._remove_wrapper(list(node["inner"])[0])
        except:
            pass
        return node

    @staticmethod
    def _remove_ids(json_node):
        if not isinstance(json_node, dict):
            return json_node
        return {k: v for k, v in json_node.items() if not k in ID_TAGS}

    @staticmethod
    def _is_reference(json_node):
        return len(ReferenceHelper._get_reference_ids(json_node)) > 0

    @staticmethod
    @cache
    def __is_property(key):
        return key not in [
            "id",
            "inner",
            "loc",
            "range",
            "kind",
            "name",
            "isUsed",
            "isReferenced",
            "referencedDecl",
            "mangledName",
            *ON_NODE_ID_TAGS,
        ]

    @staticmethod
    def _is_wrapped(node):
        """
        Check if a node is wrapped.

        A node is considered wrapped if it meets the following conditions:
        1. The node does not have an 'id' or its 'kind' starts with "Implicit".
        2. The node has exactly one inner node.
        """
        return (not node.get("id") or node["kind"].startswith("Implicit")) and len(list(node["inner"])) == 1

    def _get[T](self, path: Sequence[str], default: T) -> T:
        return self._get_property(self.node, path, default)

    @staticmethod
    def _get_property[T](target: dict[str, Any], path: Sequence[str], default: T) -> T:
        assert default is not None, "default value must be provided"
        try:
            for p in path:
                target = target[p]
                # TODO: Is this code really correct when path contains multiple strings?
                # Doesn't target become an Any, and hence might not support __get_item__ any more?
            return target if isinstance(target, type(default)) else default
        except:
            return default

    @property
    def is_implicit(self):
        self.is_part_of_translation_unit()


class ReferenceHelper:

    @staticmethod
    def create_references(ast_node: ClangJsonASTNode) -> None:
        assert isinstance(
            ast_node, ClangJsonASTNode
        ), f"Expected ClangJsonASTNode but got {type(ast_node)}"  # TODO: still needed when using type hints?
        if ast_node.inserted:
            return
        references = []
        node_id = ast_node.node["id"]
        ast_node.translation_unit._references[node_id] = references
        refs = {k: v for k, v in ast_node.node.items() if not ReferenceHelper._is_child_node(k) and ClangJsonASTNode._is_reference(v)}
        for k in [k for k in ast_node.node.keys() if k in ON_NODE_ID_TAGS]:
            refs[k] = ast_node.node
            # add the node if it contains a reference for example in case of previousDecl

        # to make clang json compatible with clang python, we add the reference of the DeclRefExpr child to the CallExpr
        if ast_node._kind == "CallExpr":
            for n in ast_node.children:
                if n.kind == "DeclRefExpr":
                    refChild = {
                        k: v for k, v in n.node.items() if not ReferenceHelper._is_child_node(k) and ClangJsonASTNode._is_reference(v)
                    }
                    refs.update(refChild)

        for kind, ref in refs.items():
            for ref_id in ReferenceHelper._get_reference_ids(ref):
                if ref_id == node_id:
                    continue
                properties = {k: p for k, p in ref.items() if k != ref_id} if ref != ast_node.node else EMPTY_DICT
                reference = ClangJsonASTReference(ref_id, kind, properties)
                referenced_by = ClangJsonASTReference(node_id, kind, properties)
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                references.append(reference)

    @staticmethod
    def add_record_references(ast_node: ClangJsonASTNode) -> None:
        """
        Json does not contain direct references between classes and their base classes.

        Hence these references are created in this method.

        This method checks if the given AST node is of kind 'CXXRecordDecl' and has a tag 'class'.
        If so, it processes the base classes of the node and creates references for them.

        Args:
            ast_node (ClangJsonASTNode): The AST node to process.

        Raises:
            AssertionError: If the provided ast_node is not an instance of ClangJsonASTNode.
        """
        assert isinstance(
            ast_node, ClangJsonASTNode
        ), f"Expected ClangJsonASTNode but got {type(ast_node)}"  # TODO: still needed when using type hints?
        if ast_node.inserted:
            return

        bases = ast_node._get(["bases"], [])
        if not bases:
            bases = [ast_node.node] if ast_node.node.get("type") else None
        if not bases:
            return
        node_id = ast_node.node["id"]
        for base in bases:
            ref_ids = ReferenceHelper._get_record_decl(ast_node, base)
            for kind, ref_id in ref_ids:
                properties = {k: p for k, p in base.items() if k != "type"}
                reference = ClangJsonASTReference(ref_id, kind, properties)
                referenced_by = ClangJsonASTReference(node_id, kind, properties)
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                try:
                    ast_node.translation_unit._references[node_id].append(reference)
                except:
                    ast_node.translation_unit._references[node_id] = [reference]

    @staticmethod
    def _get_record_decl(ast_node, base) -> Sequence[str]:
        try:
            tp = base["type"]
            if "desugaredQualType" in tp and "::" in tp["desugaredQualType"]:
                # split desugaredQualType to derive the parent namespaces
                namespaces = tp["desugaredQualType"].split("::")[:-1][::-1]
            else:
                namespaces = []
            qual_type = tp["qualType"]
            ids = []
            ctorType = EMPTY_STR
            if ast_node.kind == "CXXConstructExpr":
                ctorType = ast_node._get(["ctorType", "qualType"], EMPTY_STR)

            for id, node in ast_node.translation_unit._nodes.items():
                if node.kind == "CXXRecordDecl" and node.name == qual_type:
                    parent = node.parent
                    matches = True
                    for ns in namespaces:
                        if ns != parent.name or parent.kind != "NamespaceDecl":
                            matches = False
                        parent = parent.parent
                    if matches:
                        ids.append((node.kind, id))
                if ctorType != EMPTY_STR and node.kind == "CXXConstructorDecl":
                    # link all matching
                    matches = node._get(["type", "qualType"], EMPTY_STR) == ctorType
                    if matches:
                        ids.append((node.kind, id))
            return ids
        except:
            pass
        return []

    @staticmethod
    def _get_reference_ids(json_node):
        result = []
        if not isinstance(json_node, dict):
            return result
        for key in ID_TAGS:
            value = json_node.get(key)
            if value != None:
                result.append(value)
        return result

    @staticmethod
    @cache
    def _is_child_node(key):
        return key in ["inner"]
