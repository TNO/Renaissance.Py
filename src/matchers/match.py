from lst.lst import LSTNode
from matchers.pattern_matcher import MatchResult
from typing import List, Optional


class Match:
    def __init__(self, result: MatchResult):
        self._result = result

    def placeholders(self) -> List[str]:
        return list(self._result.bindings.keys())

    def get(self, name: str) -> List[LSTNode]:
        return self._result.bindings.get(name, [])

    def first(self, name: str) -> Optional[LSTNode]:
        return self.get(name)[0] if self.get(name) else None

    def __repr__(self):
        items = ', '.join(f'${k}: {v[0].signature.strip()[:30]!r}...' for k, v in self._result.bindings.items())
        return f"Match({items})"
