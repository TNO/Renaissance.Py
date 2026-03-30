from typing import Any, Self


class GoAstNode:
    @property
    def properties(self) -> dict[str, Any]:
        ...

    @property
    def children(self) -> list[Self]:
        ...