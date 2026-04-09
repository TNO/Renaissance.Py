from typing import Any, Self, Sequence


class GoAstNode:
    # direct access protocol
    expr: Self
    body: Sequence[Self]
    other: Sequence[Self]

    # rewrite protocol
    length: int
    offset: int
    name: str

    @property
    def properties(self) -> dict[str, Any]:
        return {"length": self.length, "offset": self.offset, "name": self.name}

    children: list[Self] = []

    @property
    def children(self) -> list[Self]:
        return [self.expr, self.body, self.other]
