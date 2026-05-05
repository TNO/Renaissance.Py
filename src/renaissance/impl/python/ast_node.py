"""
implementation that patches the native ast using 'traits' mechanism,
require minimum amound of code to make the matcher work

"""

import ast

from renaissance.impl.types import KIND_MAP, UnknownKind


class ASTExtension:

    @staticmethod
    def load_from_ast(text, file):
        root = ast.parse(text, file)
        return root

    @staticmethod
    @property
    def ast_node(self):
        return self

    @staticmethod
    @property
    def ast_kind(self):
        return KIND_MAP.get(type(self).__name__, UnknownKind).__name__

    @staticmethod
    @property
    def ast_properties(self):
        return {field: getattr(self, field) for field in self._fields if not isinstance(getattr(self, field), ast.AST)}

    @staticmethod
    @property
    def ast_children(self):
        children = [getattr(self, field) for field in self._fields if isinstance(getattr(self, field), (ast.AST))]
        [children.extend(getattr(self, field)) for field in self._fields if isinstance(getattr(self, field), (list))]
        return children

    @staticmethod
    @property
    def ast_signature(self):
        return ast.unparse(self)

    @staticmethod
    @property
    def ast_name(self):
        return str(self)
