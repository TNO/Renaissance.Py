from ast import AST
from typing import Any

'''
implementation that patches the native ast using 'traits' mechanism,
require minimum amound of code to make the matcher work
 
'''


@property
def properties(self:AST) -> dict[str, Any]:
        props={}
        for name in self._fields:
            props[name]= getattr(self, name)
        return props
AST.properties=properties

@property
def children(self: AST) -> list[AST]:
    return getattr(self, 'body', [])
AST.children = children


def is_part_of_translation_unit(_:AST):
    return True

AST.is_part_of_translation_unit = is_part_of_translation_unit


@property
def kind(self:AST):
    return str(type(self).__name__)
AST.kind = kind


def raw(self):
    return f"({self.kind})\n"
AST.__str__ = raw