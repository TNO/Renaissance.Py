from typing import Sequence, Self, Iterable, Protocol, runtime_checkable

from more_itertools import flatten

from renaissance.impl import MATCH_ALL, MATCH_ONE
from ..utils.ast_utils import use_dollar


IRRELEVANT_PROPS = {"macro_expansion", "start_point", "end_point", "source_code", "location", "type"}
DEFAULT_EXCLUDE_KIND = {"FullComment", "MACRO_DEFINITION", "Comment"}
MIS_MATCH = -2
INCOMPLETE_MATCH = -1


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
        return [
            m for node in self.nodes for ref in node.referenced_by
            for pattern in patterns for m in MatchFinder.match_pattern([ref.node], pattern, recursive)
        ]

    def match_references(self, patterns: Iterable[list], recursive: bool = True) -> Sequence[Self]:
        return [
            m for node in self.nodes for ref in node.references
            for pattern in patterns for m in MatchFinder.match_pattern([ref.node], pattern, recursive)
        ]


def is_match_tree(src: Sequence | None, cmp: Sequence | None, expansions=None):
    if expansions is None:
        expansions = {}
    if not (isinstance(src, list) and isinstance(cmp, list)) or len(cmp) == 0 or len(src) == 0:
        return src == cmp
    if len(cmp) == 1 and isinstance(cmp0 := cmp[0], AstProtocol) and cmp0.kind == MATCH_ALL:
        expansions[cmp0.name] = src
        return True
    return find_in_list(src, cmp, expansions, 0) == len(src) - 1


def variant_in_match_stmt(src: AstProtocol, cmp: AstProtocol, expansions) -> list:
    if cmp.kind == MATCH_ONE and cmp.name:
        if cmp.name in expansions:
            if src == expansions[cmp.name][0]:
                return [Variant(0, expansions, None, 0, 0)]
        else:
            expansions[cmp.name] = [src]
            return [Variant(0, expansions, None, -1, 0)]
        return []
    if is_match_dict(src.properties, cmp.properties, expansions) and src.kind == cmp.kind:
        exprs = exclude_nodes_by_kind(src.children)
        cmp_exprs = exclude_nodes_by_kind(cmp.children)
        if len(cmp_exprs) == 0 and len(exprs) > 0:
            return []
        variants = trim_invalid_variants(exprs, cmp_exprs, find_variants(exprs, cmp_exprs, expansions))
        return [v for v in variants if v.end_index == len(exprs) - 1]
    return []


def find_variants(src: Sequence, cmp: Sequence, expansion=None, start: int = 0):
    if expansion is None:
        expansion = {}
    i = start
    variants = [Variant(0, expansion, None, -1)]
    expansion = {}
    new_variants = []
    while i < len(src):
        for variant in variants:
            if variant.end_index is not INCOMPLETE_MATCH:
                continue

            if variant.index == len(cmp):
                variant.end_index = i - 1
            else:
                while cmp[variant.index].kind == MATCH_ALL:
                    if variant.expansion_start == -1:
                        variant.expansion_start = i
                        variant.greedy = cmp[variant.index].name
                    elif cmp[variant.index].name != variant.greedy and variant.greedy not in variant.exp:
                        new_variants.append(Variant(variant.index, variant.exp.copy(), variant.greedy, variant.expansion_start))
                        variant.exp[variant.greedy] = src[variant.expansion_start:i]
                        variant.greedy = cmp[variant.index].name
                        variant.expansion_start = i
                    else:
                        break
                    if (variant.index + 1) < len(cmp) and (
                        cmp[variant.index].name not in variant.exp or variant.exp[cmp[variant.index].name] == []
                    ):
                        variant.index += 1
                    else:
                        break

            if variant.index == len(cmp):
                continue

            if (
                cmp[variant.index].kind != MATCH_ALL
                and len(child_variants := variant_in_match_stmt(src[i], cmp[variant.index], variant.exp)) > 0
            ):
                if variant.greedy is not None and variant.expansion_start != -1 and variant.greedy not in variant.exp:
                    new_variants.append(Variant(variant.index, variant.exp.copy(), variant.greedy, variant.expansion_start))
                    new_variants[-1].exp.pop(cmp[variant.index].name, None)
                    variant.exp[variant.greedy] = src[variant.expansion_start:i]
                    variant.greedy = None
                    variant.expansion_start = -1
                if len(child_variants) > 1:
                    for v in child_variants:
                        new_variants.append(Variant(variant.index + 1, v.exp, variant.greedy, variant.expansion_start, INCOMPLETE_MATCH))
                    variant.end_index = MIS_MATCH
                else:
                    variant.exp = child_variants[0].exp
                    variant.index += 1
                    if i == len(src) - 1 and variant.index == len(cmp):
                        variant.end_index = len(src) - 1
            elif variant.greedy:
                exp_index = i - variant.expansion_start
                if variant.greedy not in variant.exp:
                    if i == len(src) - 1 and variant.greedy == cmp[variant.index].name:
                        variant.exp[variant.greedy] = src[variant.expansion_start:i + 1]
                        variant.greedy = None
                        variant.expansion_start = -1
                        variant.end_index = i
                        variant.index += 1
                elif exp_index < len(variant.exp[cmp[variant.index].name]):
                    if src[i] != variant.exp[cmp[variant.index].name][exp_index]:
                        variant.end_index = MIS_MATCH
                    else:
                        if i - variant.expansion_start == len(variant.exp[cmp[variant.index].name]) - 1:
                            variant.greedy = None
                            variant.expansion_start = -1
                            variant.index += 1
                else:
                    variant.greedy = None
                    variant.expansion_start = -1
                    variant.index += 1
            else:
                if variant.end_index == INCOMPLETE_MATCH:
                    variant.end_index = MIS_MATCH

        variants.extend(new_variants)
        new_variants = []
        variants = [v for v in variants if v.end_index != MIS_MATCH]
        i += 1

    return variants


def trim_invalid_variants(src, cmp, variants):
    full_match = len(src) - 1
    valid_variants = []
    for variant in variants:
        if variant.end_index == MIS_MATCH or variant.index < len(cmp) - 1:
            continue
        if variant.index == len(cmp) - 1:
            if cmp[variant.index].kind == MATCH_ALL and cmp[variant.index].name not in variant.exp:
                key = variant.greedy if variant.expansion_start != -1 else cmp[variant.index].name
                variant.exp[key] = src[variant.expansion_start:] if variant.expansion_start != -1 else []
                variant.end_index = full_match
                valid_variants.append(variant)
        elif variant.index == len(cmp):
            if variant.greedy and variant.greedy not in variant.exp:
                variant.exp[variant.greedy] = src[variant.expansion_start:]
                variant.end_index = full_match
            elif variant.end_index == INCOMPLETE_MATCH:
                variant.end_index = full_match
            valid_variants.append(variant)
        else:
            valid_variants.append(variant)
    return valid_variants


def find_in_list(src: Sequence, cmp: Sequence, exp=None, start: int = 0):
    if exp is None:
        exp = {}
    variants = find_variants(src, cmp, exp, start)
    variants = trim_invalid_variants(src, cmp, variants)
    if not variants:
        return -1
    exp.update(variants[-1].exp)
    return variants[-1].end_index


def is_match(src: AstProtocol, cmp: AstProtocol, expansions=None) -> bool:
    if expansions is None:
        expansions = {}
    assert isinstance(src, AstProtocol)
    assert isinstance(cmp, AstProtocol)
    if src.kind not in ["Module", "TRANSLATION_UNIT"] and cmp.kind == MATCH_ONE and cmp.name:
        if cmp.name in expansions:
            return is_match(src, expansions[cmp.name][0])
        expansions[cmp.name] = [src]
        return True
    if cmp.kind != src.kind:
        return False
    return (
        is_match_dict(src.properties, cmp.properties, expansions)
        and is_match_tree(exclude_nodes_by_kind(src.children), cmp.children, expansions)
    )


def exclude_nodes_by_kind(src: list[AstProtocol]) -> list[AstProtocol]:
    return [c for c in src if c.kind not in DEFAULT_EXCLUDE_KIND]


def is_match_dict(src: dict, cmp: dict, expansions: dict = None) -> bool:
    if expansions is None:
        expansions = {}

    def match_property(n):
        c = cmp.get(n)
        s = src.get(n)
        if isinstance(c, str) and (key := use_dollar(c)).startswith("$"):
            if c in expansions:
                return s == expansions[key][0]
            expansions[key] = [s]
            return True
        return s == c

    all_keys = (src.keys() | cmp.keys()) - IRRELEVANT_PROPS
    return all(match_property(n) for n in all_keys)


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
                    MatchFinder.match_pattern(
                        exclude_nodes_by_kind(getattr(src_nodes[to_do], "children", [])),
                        patterns,
                        recursive,
                    )
                )
            to_do += 1
    return found_statements


def find_all(src_nodes, *patterns, recursive: bool = True) -> Sequence[PatternMatch]:
    return list(flatten(MatchFinder.match_pattern(src_nodes, pattern, recursive) for pattern in patterns))


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
