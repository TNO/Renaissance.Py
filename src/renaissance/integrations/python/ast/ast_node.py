"""Implementation that patches the native ast using 'traits' mechanism.

Requires minimum amount of code to make the matcher work.
"""

import ast

from renaissance.integrations.python.ast.kinds import PYTHON_KIND_MAP
from renaissance.syntax_tree.semantic_kind import SemanticKind


class ASTExtension:
    """AI: Static trait methods patched onto the stdlib ast.AST class to satisfy the node protocol."""

    @staticmethod
    def load_from_ast(text, file):
        """AI: Parse text as Python source (attributed to file) into a native ast.AST tree."""
        root = ast.parse(text, file)
        return root

    @staticmethod
    @property
    def ast_node(self):
        """AI: Return this node itself."""
        return self

    @staticmethod
    @property
    def parser_kind(self):
        """AI: Return this node's ast class name as its parser kind."""
        return type(self).__name__

    @staticmethod
    @property
    def semantic_kind(self):
        """AI: Return the semantic kind mapped from this node's ast class name."""
        return PYTHON_KIND_MAP.get(type(self).__name__, SemanticKind.NODE)

    @staticmethod
    @property
    def ast_properties(self):
        """AI: Return this node's non-AST fields as a name-to-value dict."""
        return {field: getattr(self, field) for field in self._fields if not isinstance(getattr(self, field), ast.AST)}

    @staticmethod
    @property
    def ast_children(self):
        """AI: Return this node's direct child AST nodes, including those held in list fields."""
        children = [getattr(self, field) for field in self._fields if isinstance(getattr(self, field), (ast.AST))]
        [children.extend(getattr(self, field)) for field in self._fields if isinstance(getattr(self, field), (list))]
        return children

    @staticmethod
    @property
    def ast_signature(self):
        """AI: Return the unparsed source text of this node."""
        return ast.unparse(self)

    @staticmethod
    @property
    def ast_name(self):
        """AI: Return this node's identifying name, derived from its specific ast node type."""
        if isinstance(self, ast.arg):
            signature = self.arg
        elif isinstance(self, ast.Name):
            signature = self.id
        elif isinstance(self, ast.Expr) and isinstance(self.value, ast.Name):
            signature = self.value.id
        else:
            signature = str(self)
        return signature
