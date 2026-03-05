from ast import AST,If
from typing import Sequence, Any


def properties(self:AST) -> dict[str, Any]:
        props={}
        for name in self._fields:
            props[name]= getattr(self, name)
        return props

AST.properties=properties
def ast_children(self:AST) -> list[AST]:
    return []

@property
def ast_children(self: AST) -> list[AST]:
    return self.body if 'body' in self._fields else []
AST.children = ast_children


def is_part_of_translation_unit(self:AST):
    return True

AST.is_part_of_translation_unit = is_part_of_translation_unit

class ImplicitNode():
    def __init__(self, name, children):
        self.name = name
        self.children = children
        self.kind ='implicit'
    def is_part_of_translation_unit(self: AST):
        return True
    def __str__(self):
        return f"{self.kind} {self.name}\n"
@property
def children(self:If) -> list[AST]:
    return [self.test, ImplicitNode('body',self.body)] #, ImplicitNode('orelse',self.orelse)]
If.children = children

@property
def kind(self:AST):
    return str(type(self).__name__)
AST.kind = kind


def raw(self):
    return f"({self.kind})\n"
AST.__str__ = raw