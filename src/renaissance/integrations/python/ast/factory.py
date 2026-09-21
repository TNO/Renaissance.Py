"""AI: Factories for creating Python AST/pattern nodes for parsing and pattern matching."""

import ast
import re
from collections.abc import Sequence
from pathlib import Path

import tree_sitter_python
from libcst import SimpleStatementLine

from renaissance.integrations import MATCH_ALL, MATCH_ONE
from renaissance.integrations.python.ast.ast_node import ASTExtension
from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.match_finder import is_match
from renaissance.syntax_tree.node_protocol import NodeProtocol
from renaissance.syntax_tree.pattern_kind import PatternKind
from renaissance.utils.ast_utils import replace_dollar, use_dollar

_MATCH_ALL_RE = re.compile(r"^" + re.escape(MATCH_ALL) + r"\w+$")
_MATCH_ONE_RE = re.compile(r"^" + re.escape(MATCH_ONE) + r"\w+$")

SHOW_NODE = False


class PythonPattern(NodeProtocol):
    """AI: Wrap a Python AST/RST node as a matchable pattern, detecting match-all/match-one placeholders."""

    def __init__(self, node):
        """AI: Wrap a Python AST/RST node as a matchable pattern, detecting match-all/match-one placeholders."""
        self.node: PythonRstNode = node
        if type(node) is str:
            print(node)
            return
        self.parser_kind = getattr(node, "parser_kind", type(node).__name__)
        self.semantic_kind = getattr(node, "semantic_kind", None)
        self.pattern_kind = None
        self._derive_pattern_kind(node)

        self.properties: dict = node.properties
        self.children: list[PythonPattern] = [PythonPattern(node) for node in node.children]
        self.signature: str = node.signature
        if hasattr(node, "name") and node.name:
            self.name: str = use_dollar(node.name)
        else:
            self.name = ""

    def __eq__(self, other: NodeProtocol) -> bool:
        """AI: Return whether `other` matches this pattern node."""
        return is_match(other, self)

    def __repr__(self):
        """AI: Return a dollar-escaped repr of the wrapped node."""
        return use_dollar(str(self.node))

    def _derive_pattern_kind(self, node) -> None:
        if isinstance(node, ast.arg):
            signature = node.arg
        elif isinstance(node, ast.Name):
            signature = node.id
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Name):
            signature = node.value.id
        elif isinstance(node, ast.AST):
            signature = str(node)
        else:
            signature = node.name

        if node.parser_kind in {"Name", "Expr", "arg", "Param"}:
            if _MATCH_ALL_RE.match(signature):
                self.pattern_kind = PatternKind.MATCH_ALL
            elif _MATCH_ONE_RE.match(signature):
                self.pattern_kind = PatternKind.MATCH_ONE


class PythonFactory:
    """AI: Factory for creating Python AST nodes of a configured node-implementation type."""

    def __init__(self, clazz: type[PythonRstNode | PythonCstNode | LSTNode | ast.AST]) -> None:
        """AI: Configure a factory that creates Python AST nodes of the given node-implementation type."""
        self.clazz = clazz
        if clazz == LSTNode:
            clazz.load_from_text = self.load_from_lst
        elif clazz == ast.AST:
            clazz.load_from_text = ASTExtension.load_from_ast
            # matcher
            clazz.node = ASTExtension.ast_node

            # clazz.name = ASTExtension.ast_name
            clazz.parser_kind = ASTExtension.parser_kind
            clazz.semantic_kind = ASTExtension.semantic_kind
            clazz.properties = ASTExtension.ast_properties
            clazz.children = ASTExtension.ast_children
            clazz.signature = ASTExtension.ast_signature

            # writer
            clazz.text = ASTExtension.ast_signature
            clazz.filename = "dummy.py"

            # shower
            clazz.is_implicit = True
            clazz.show_props = False
            clazz.indent = ""

    def create(self, file_path: Path) -> PythonRstNode | PythonCstNode:
        """AI: Parse the Python source file at file_path into an AST node tree."""
        atu = self.clazz.load(file_path=file_path)
        assert isinstance(atu, self.clazz)
        return atu

    def create_from_text(self, text: str, file_name: str = "snippet.py") -> PythonRstNode | PythonCstNode | LSTNode | ast.AST:
        """AI: Parse Python source text (attributed to file_name) into an AST node tree."""
        atu = self.clazz.load_from_text(text, file_name)
        assert isinstance(atu, self.clazz)
        return atu

    @staticmethod
    def load_from_lst(text: str, _file_name: str) -> LSTNode:
        """AI: Parse Python source text with tree-sitter into an LST node tree."""
        adapter = TreeSitterAdapter(tree_sitter_python)
        tree = adapter.parse_code(text)
        return adapter.to_lst(text, tree).root


class PythonPatternFactory:
    """AI: Factory for building Python AST patterns from text."""

    def __init__(self, factory: PythonFactory):
        """AI: Prepare a pattern factory for creating Python AST patterns from text."""
        self.factory = factory

    def _create(self, text: str) -> PythonPattern:
        return PythonPattern(self.factory.create_from_text(text, "pattern.py"))

    def create(self, text: str) -> PythonPattern:
        """AI: Parse text as a Python pattern, substituting placeholder dollar syntax first."""
        text = replace_dollar(text)
        return self._create(text)

    def create_statements(self, text: str) -> Sequence[PythonPattern]:
        """AI: Parse text and return its top-level statement pattern nodes."""
        atu = self.create(text)
        return atu.children

    def create_statement(self, text: str) -> PythonPattern:
        """AI: Parse text and return its last top-level statement pattern node."""
        stmt = self.create_statements(text)[-1]
        if isinstance(stmt.node.node, SimpleStatementLine):
            return stmt.children[0]
        return stmt
        # return stmt

    def create_expression(self, text: str) -> PythonPattern:
        """AI: Parse text and return the expression pattern node of its last statement."""
        my_pattern = self.create_statement(text)
        if isinstance(my_pattern.node, PythonRstNode):
            return PythonPattern(my_pattern.node.expression)
        if isinstance(my_pattern.node, (LSTNode, PythonCstNode)):
            return PythonPattern(my_pattern.node.children[-1])
        return PythonPattern(my_pattern.node.children[0])

    def create_decorators(self, param):
        """AI: Parse param as a decorator applied to a dummy test function and return the decorator pattern node."""
        return self.create_statement(param + "\ndef test(): pass").children[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        """AI: Parse kw_str as call keyword arguments and return their pattern nodes."""
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "kwarg_pattern.py", type_comments=True).body[0].value
        return [PythonPattern(PythonRstNode(kwarg)) for kwarg in call.keywords]
