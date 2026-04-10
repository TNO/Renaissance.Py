from typing import Sequence, Self, Iterable, Protocol, runtime_checkable

from renaissance.impl import MATCH_ALL, MATCH_ONE
from ..utils.ast_utils import use_dollar


IRRELEVANT_PROPS = {"macro_expansion", "start_point", "end_point", "source_code", "location", "type"}
MIS_MATCH = -2
INCOMPLETE_MATCH = -1
_TOP_LEVEL_KINDS = {"Module", "TRANSLATION_UNIT"}


@runtime_checkable
class AstProtocol(Protocol):
    kind: str
    properties: dict
    children: list[Self]
    signature: str
    name: str


class Variant:
    def __init__(self, index, exp, greedy, expansion_start, end_index=INCOMPLETE_MATCH):
        self.exp: dict = exp
        self.index: int = index
        self.greedy: str = greedy
        self.end_index = end_index
        self.expansion_start = expansion_start

    def reset_greedy(self):
        self.greedy = None
        self.expansion_start = -1

    def close_greedy(self, key, value):
        """Store a completed greedy expansion and reset greedy state."""
        self.exp[key] = value
        self.reset_greedy()

    def fork(self) -> "Variant":
        """Return a copy of this variant at the same position (for backtracking)."""
        return Variant(self.index, self.exp.copy(), self.greedy, self.expansion_start)


class PatternMatch:
    def __init__(self, nodes, expansions, patterns):
        self.nodes = nodes
        self.expansions = expansions
        self.patterns = patterns

    def __str__(self):
        return "\n".join(node.signature for node in self.nodes)

    @property
    def signature(self):
        return str(self)

    def __getitem__(self, key):
        return "\n".join(node.signature if isinstance(node, AstProtocol) else node for node in self.expansions[key])

    def match_referenced_by(self, patterns: Sequence[list], recursive: bool = True) -> Sequence[Self]:
        return self._match_relations("referenced_by", patterns, recursive)

    def match_references(self, patterns: Iterable[list], recursive: bool = True) -> Sequence[Self]:
        return self._match_relations("references", patterns, recursive)

    def _match_relations(self, attr: str, patterns, recursive: bool) -> list:
        return [
            m for node in self.nodes for ref in getattr(node, attr)
            for pattern in patterns for m in MatchFinder.match_pattern([ref.node], pattern, recursive)
        ]


def _resolve_match_one(name: str, src: "AstProtocol", expansions: dict):
    """Handle a MATCH_ONE pattern node: bind or verify the named expansion. Returns True if matched."""
    if name in expansions:
        return src == expansions[name][0]
    expansions[name] = [src]
    return True


def is_match_tree(src: Sequence | None, cmp: Sequence | None, expansions=None):
    if expansions is None:
        expansions = {}
    both_lists = isinstance(src, list) and isinstance(cmp, list)
    if not both_lists or not cmp or not src:
        return src == cmp
    single_match_all = len(cmp) == 1 and isinstance(cmp0 := cmp[0], AstProtocol) and cmp0.kind == MATCH_ALL
    if single_match_all:
        expansions[cmp0.name] = src
        return True
    return find_in_list(src, cmp, expansions, 0) == len(src) - 1


def variant_in_match_stmt(src: AstProtocol, cmp: AstProtocol, expansions) -> list:
    if cmp.kind == MATCH_ONE and cmp.name:
        matched = _resolve_match_one(cmp.name, src, expansions)
        return [Variant(0, expansions, None, 0, 0)] if matched else []
    if is_match_dict(src.properties, cmp.properties, expansions) and src.kind == cmp.kind:
        exprs = src.children
        cmp_exprs = cmp.children
        if not cmp_exprs and exprs:
            return []
        variants = find_variants(exprs, cmp_exprs, expansions)
        return [v for v in variants if v.end_index == len(exprs) - 1]
    return []

def _advance_match_all(variant: Variant, cmp: Sequence, src: Sequence, i: int, new_variants: list):
    """Advance variant.index past consecutive MATCH_ALL pattern nodes, forking new_variants as needed."""
    while cmp[variant.index].kind == MATCH_ALL:
        current_name = cmp[variant.index].name
        if variant.expansion_start == -1:
            variant.expansion_start = i
            variant.greedy = current_name
        elif current_name != variant.greedy and variant.greedy not in variant.exp:
            new_variants.append(variant.fork())
            variant.close_greedy(variant.greedy, src[variant.expansion_start:i])
            variant.greedy = current_name
            variant.expansion_start = i
        else:
            break
        has_next = (variant.index + 1) < len(cmp)
        not_yet_expanded = current_name not in variant.exp or variant.exp[current_name] == []
        if has_next and not_yet_expanded:
            variant.index += 1
        else:
            break


def _apply_child_match(variant: Variant, child_variants: list, cmp: Sequence, src: Sequence, i: int, new_variants: list):
    """Apply a successful child match, forking if there are multiple child variants."""
    greedy_open = variant.greedy is not None and variant.expansion_start != -1 and variant.greedy not in variant.exp
    if greedy_open:
        forked = variant.fork()
        forked.exp.pop(cmp[variant.index].name, None)
        new_variants.append(forked)
        variant.close_greedy(variant.greedy, src[variant.expansion_start:i])
    if len(child_variants) > 1:
        for v in child_variants:
            new_variants.append(Variant(variant.index + 1, v.exp, variant.greedy, variant.expansion_start, INCOMPLETE_MATCH))
        variant.end_index = MIS_MATCH
    else:
        variant.exp = child_variants[0].exp
        variant.index += 1
        reached_end = i == len(src) - 1 and variant.index == len(cmp)
        if reached_end:
            variant.end_index = len(src) - 1


def _advance_greedy(variant: Variant, cmp: Sequence, src: Sequence, i: int):
    """Accumulate or verify greedy expansion for the current source node."""
    exp_for_key = variant.exp.get(cmp[variant.index].name)
    exp_index = i - variant.expansion_start
    if exp_for_key is None:
        at_last_src_node = i == len(src) - 1
        greedy_matches_pattern = variant.greedy == cmp[variant.index].name
        if at_last_src_node and greedy_matches_pattern:
            variant.close_greedy(variant.greedy, src[variant.expansion_start:i + 1])
            variant.end_index = i
            variant.index += 1
    elif exp_index < len(exp_for_key):
        src_node_matches = src[i] == exp_for_key[exp_index]
        expansion_complete = exp_index == len(exp_for_key) - 1
        if not src_node_matches:
            variant.end_index = MIS_MATCH
        elif expansion_complete:
            variant.reset_greedy()
            variant.index += 1
    else:
        variant.reset_greedy()
        variant.index += 1


def find_variants(src: Sequence, cmp: Sequence, expansion=None, start: int = 0):
    if expansion is None:
        expansion = {}
    i = start
    variants = [Variant(0, expansion, None, -1)]
    while i < len(src):
        next_variants = []
        for variant in variants:
            if variant.end_index is not INCOMPLETE_MATCH:
                next_variants.append(variant)
                continue
            if variant.index == len(cmp):
                variant.end_index = i - 1
                next_variants.append(variant)
                continue
            _advance_match_all(variant, cmp, src, i, next_variants)
            if variant.index == len(cmp):
                next_variants.append(variant)
                continue
            if (
                cmp[variant.index].kind != MATCH_ALL
                and (child_variants := variant_in_match_stmt(src[i], cmp[variant.index], variant.exp))
            ):
                _apply_child_match(variant, child_variants, cmp, src, i, next_variants)
            elif variant.greedy:
                _advance_greedy(variant, cmp, src, i)
            else:
                variant.end_index = MIS_MATCH
            if variant.end_index != MIS_MATCH:
                next_variants.append(variant)
        variants = next_variants
        i += 1

    full_match = len(src) - 1
    valid_variants = []
    for variant in variants:
        if variant.end_index == MIS_MATCH or variant.index < len(cmp) - 1:
            continue
        if variant.index == len(cmp) - 1:
            last_cmp = cmp[variant.index]
            trailing_wildcard = last_cmp.kind == MATCH_ALL and last_cmp.name not in variant.exp
            if not trailing_wildcard:
                continue
            key = variant.greedy if variant.expansion_start != -1 else last_cmp.name
            variant.close_greedy(key, src[variant.expansion_start:] if variant.expansion_start != -1 else [])
        elif variant.index == len(cmp):
            greedy_unresolved = variant.greedy and variant.greedy not in variant.exp
            if greedy_unresolved:
                variant.close_greedy(variant.greedy, src[variant.expansion_start:])
        if variant.end_index == INCOMPLETE_MATCH:
            variant.end_index = full_match
        valid_variants.append(variant)
    return valid_variants

def find_in_list(src: Sequence, cmp: Sequence, exp=None, start: int = 0):
    if exp is None:
        exp = {}
    variants =  find_variants(src, cmp, exp, start)
    if not variants:
        return -1
    exp.update(variants[0].exp)
    # [0] most greedy
    # [-1] least greedy
    return variants[0].end_index


def is_match(src: AstProtocol, cmp: AstProtocol, expansions=None) -> bool:
    return variant_in_match_stmt(src, cmp, expansions)!=[]

def is_match_dict(src: dict, cmp: dict, expansions: dict = None) -> bool:
    if expansions is None:
        expansions = {}

    def match_property(n):
        c = cmp.get(n)
        s = src.get(n)
        if isinstance(c, str) and (key := use_dollar(c)).startswith("$"):
            return s == expansions[key][0] if key in expansions else (expansions.update({key: [s]}) or True)
        return s == c

    return all(match_property(n) for n in (src.keys() | cmp.keys()) - IRRELEVANT_PROPS)


def match_pattern(src_nodes, patterns, recursive=True) -> Sequence[PatternMatch]:
    found_statements = []
    to_do = 0
    while to_do < len(src_nodes):
        found_expansions = {}
        found_position = find_in_list(src_nodes, patterns, found_expansions, to_do)
        if found_position >= 0:
            found_statements.append(PatternMatch(src_nodes[to_do:found_position + 1], found_expansions, patterns))
            to_do = found_position + 1
        else:
            if recursive:
                found_statements.extend(
                    match_pattern(getattr(src_nodes[to_do], "children", []), patterns, recursive)
                )
            to_do += 1
    return found_statements


def find_all(src_nodes, *patterns, recursive: bool = True) -> Sequence[PatternMatch]:
    return [m for pattern in patterns for m in match_pattern(src_nodes, pattern, recursive)]


class MatchFinder:
    @staticmethod
    def find_all(
        src_nodes: Sequence[AstProtocol],
        *patterns: Sequence[AstProtocol],
        recursive: bool = True,
    ) -> Sequence[PatternMatch]:
        """Finds all pattern matches in the given source nodes."""
        return find_all(src_nodes, *patterns, recursive=recursive)

    @staticmethod
    def match_pattern(
        src_nodes: Sequence[AstProtocol],
        patterns: Sequence[AstProtocol],
        recursive: bool = True,
    ) -> Sequence[PatternMatch]:
        """Matches source nodes against a list of pattern nodes, optionally recursing into children."""
        return match_pattern(src_nodes, patterns, recursive)


# We should find the highest possible match.
# For example in C++:
#   "int $x; $x;"                                   matches "int x; x;"
#   "int $x = 1; int y = $x;"                       matches "int x = 1; int y = x;"
#   "typedef enum { $x } E; void f() { g($x); }"   matches "typedef enum { x } E; void f() { g(x); }"
# The highest shared type should be chosen as the type of $x.
