from dataclasses import dataclass, field
from typing import Optional, Dict, List
from lst.lst import LSTNode


@dataclass
class Symbol:
    name: str
    kind: str  # e.g., 'variable', 'function'
    declared_in: Optional[LSTNode] = None
    defined_in: Optional[LSTNode] = None
    used_in: List[LSTNode] = field(default_factory=list)


class SymbolTable:
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}

    def add_declaration(self, name: str, node: LSTNode, kind: str):
        if name not in self.symbols:
            self.symbols[name] = Symbol(name, kind, declared_in=node)
        else:
            self.symbols[name].declared_in = node

    def add_definition(self, name: str, node: LSTNode):
        if name in self.symbols:
            self.symbols[name].defined_in = node
        else:
            self.symbols[name] = Symbol(name, "unknown", defined_in=node)

    def add_usage(self, name: str, node: LSTNode):
        if name not in self.symbols:
            self.symbols[name] = Symbol(name, "unknown")
        self.symbols[name].used_in.append(node)

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)
