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
    def __init__(self, index, exp, greedy, expansion_start, end_index=-1):
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
        self.variant = 0

    def __str__(self):
        return "\n".join(node.signature for node in self.nodes)

    @property
    def signature(self):
        return str(self)

    def __getitem__(self, key):
        return "\n".join(node.signature if isinstance(node, AstProtocol) else node for node in self.expansions[key])

    def match_referenced_by(self, patterns: Sequence[list], recursive: bool = True) -> Sequence[Self]:
        found_matches = []
        for node in self.nodes:
            for ref in node.referenced_by:
                for pattern in patterns:
                    found_matches.extend(MatchFinder.match_pattern([ref.node], pattern, recursive))
        return found_matches

    def match_references(self, patterns: Iterable[list], recursive: bool = True) -> Sequence[Self]:
        found_matches = []
        for node in self.nodes:
            for ref in node.references:
                for pattern in patterns:
                    found_matches.extend(MatchFinder.match_pattern([ref.node], pattern, recursive))
        return found_matches


def is_match_tree(src: Sequence | None, cmp: Sequence | None, expansions=None):
    if expansions is None:
        expansions = {}
    if cmp is None or src is None:
        return src == cmp
    # src and cmp  are both not None
    if not (isinstance(src, list) and isinstance(cmp, list)):
        return src == cmp
    # src and cmp are both lists
    if len(cmp) == 0 or len(src) == 0:
        return src == cmp
    if len(cmp) == 1 and isinstance(cmp0 := cmp[0], AstProtocol) and cmp0.kind == MATCH_ALL:
        expansions[cmp0.name] = src
        return True
    return find_in_list(src, cmp, expansions, 0) + 1 == len(src)


def variant_in_match_stmt(src: AstProtocol, cmp: AstProtocol, expansions) -> list:
    if cmp.kind == MATCH_ONE and cmp.name:
        if cmp.name in expansions:
            if src == expansions[cmp.name][0]:
                return [Variant(0, expansions, None, 0, 0)]
            # return variant_in_match_stmt(src, expansions[cmp.name][0], expansions)
        else:
            expansions[cmp.name] = [src]
            return [Variant(0, expansions, None, -1, 0)]
    elif is_match_dict(src.properties, cmp.properties, expansions) and src.kind == cmp.kind:
        exprs = exclude_nodes_by_kind(src.children)
        variants = find_variants(exprs, cmp.children, expansions)
        variants = trim_invalid_variants(exprs, cmp.children, variants)
        return [v for v in variants if v.end_index == len(exprs)-1]
    return []


def find_variants(src: Sequence, cmp: Sequence, expansion=None, start: int = 0):
    if expansion is None:
        expansion = {}
    i = start
    variants = [Variant(0, expansion, None, -1)]
    expansion = {}
    new_variants = []
    invalid_variants = []
    while i < len(src):
        for variant in variants:

            if variant.end_index is not INCOMPLETE_MATCH:
                continue

            if variant.index == len(cmp):
                variant.end_index = i - 1
            else:
                while cmp[variant.index].kind == MATCH_ALL:

                    # stranded here

                    # if cmp[variant.index].name in variant.exp:
                    #     break
                    if variant.expansion_start == -1:
                        variant.expansion_start = i
                        variant.greedy = cmp[variant.index].name
                    elif cmp[variant.index].name != variant.greedy and variant.greedy not in variant.exp:
                        # if cmp[variant.index].name not in variant.exp:
                        # exp = {key: variant.exp[key] for key in variant.exp if key in exp and key != cmp[variant.index].name}
                        new_variants.append(Variant(variant.index, variant.exp.copy(), variant.greedy, variant.expansion_start))
                        variant.exp[variant.greedy] = src[variant.expansion_start : i]
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
                if (
                    variant.greedy is not None and variant.expansion_start != -1 and variant.greedy not in variant.exp
                ):  # last_state_is_multiple:
                    # exp = {key: variant.exp[key] for key in variant.exp if key in exp and key != cmp[variant.index].name}
                    new_variants.append(Variant(variant.index, variant.exp.copy(), variant.greedy, variant.expansion_start))
                    new_variants[-1].exp.pop(cmp[variant.index].name, None)
                    variant.exp[variant.greedy] = src[variant.expansion_start : i]
                    variant.greedy = None
                    variant.expansion_start = -1
                if len(child_variants) > 1:
                    for v in child_variants:
                        new_variants.append(Variant(variant.index + 1, v.exp, variant.greedy, variant.expansion_start, INCOMPLETE_MATCH))
                    variant.end_index = MIS_MATCH
                else:
                    variant.exp = child_variants[0].exp
                    variant.index += 1
                    if i ==len(src)-1 and variant.index==len(cmp):
                        variant.end_index = len(src)-1
            elif variant.greedy:
                exp_index = i - variant.expansion_start
                if variant.greedy not in variant.exp:
                    if i==len(src)-1 and variant.greedy==cmp[variant.index].name:
                        variant.exp[variant.greedy] = src[variant.expansion_start: i+1]
                        variant.greedy = None
                        variant.expansion_start = -1
                        variant.end_index = i
                        variant.index += 1


                elif exp_index < len(variant.exp[cmp[variant.index].name]):
                    # elif exp_index < len(variant.exp[variant.greedy]):
                    if (
                        src[i] != variant.exp[cmp[variant.index].name][exp_index]
                    ):  # src[i] != variant.exp[cmp[variant.index].name][exp_index]:
                        variant.end_index = MIS_MATCH
                        invalid_variants.append(variant)
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
                    invalid_variants.append(variant)

        variants.extend(new_variants)
        new_variants = []
        # for v in invalid_variants:
        #     variants.remove(v)
        # invalid_variants = []

        i += 1
    return variants


def trim_invalid_variants(src, cmp, variants):
    full_match = len(src) - 1
    valid_variants = []
    for variant in variants:
        if variant.end_index == MIS_MATCH:
            # mismatch
            # variants.remove(variant)
            pass
        elif variant.index < len(cmp) - 1:  # incomplete
            # incomplete
            # variants.remove(variant)
            pass
        elif variant.index == len(cmp) - 1:
            if cmp[variant.index].kind == MATCH_ALL:
                if cmp[variant.index].name not in variant.exp:
                    if variant.expansion_start == -1:
                        variant.exp[cmp[variant.index].name] = []
                    else:
                        variant.exp[variant.greedy] = src[variant.expansion_start :]
                    variant.end_index = full_match
                    valid_variants.append(variant)
            # incomplete
            # variants.remove(variant)
            pass
        elif variant.index == len(cmp):
            if variant.greedy:
                if variant.greedy not in variant.exp:
                    variant.exp[variant.greedy] = src[variant.expansion_start :]
                    variant.end_index = full_match
            else:
                if variant.end_index == INCOMPLETE_MATCH:
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
    if len(variants) == 0:
        return -1
    # variant = sorted(variants, key=lambda variant: variant.end_index, reverse=True)[0]
    exp.update(variants[-1].exp)
    return variants[-1].end_index


def is_match(src: AstProtocol, cmp: AstProtocol, expansions=None) -> bool:
    if expansions is None:
        expansions = {}
    assert isinstance(src, AstProtocol)
    assert isinstance(cmp, AstProtocol)
    # 'FUNCTION_DECL',
    if src.kind not in ["Module", "TRANSLATION_UNIT"] and cmp.kind == MATCH_ONE and cmp.name:
        if cmp.name in expansions:
            return is_match(src, expansions[cmp.name][0])
        else:
            expansions[cmp.name] = [src]
            return True
    elif cmp.kind != src.kind:
        return False
    # elif isinstance(src, list) and isinstance(cmp, list):
    #     return is_match_tree(src, cmp, expansions)
    # elif isinstance(src, dict) and isinstance(cmp, dict):
    #     return is_match_dict(src, cmp, expansions)
    # elif isinstance(cmp, str):
    #     if cmp.startswith('$') or cmp.startswith(MATCH_ONE):
    #         if cmp in expansions:
    #             return is_match(src, expansions[cmp.replace(MATCH_ONE, '$')][0])
    #         else:
    #             expansions[cmp.replace(MATCH_ONE, '$')] = [src]
    #             return True
    #     return src == cmp
    elif isinstance(src, AstProtocol) and isinstance(cmp, AstProtocol):
        return is_match_dict(src.properties, cmp.properties, expansions) and is_match_tree(
            exclude_nodes_by_kind(src.children), cmp.children, expansions
        )
    else:
        return src == cmp


def exclude_nodes_by_kind(src: list[AstProtocol]) -> list[AstProtocol]:
    return [c for c in src if c.kind not in DEFAULT_EXCLUDE_KIND]


def is_match_dict(src: dict, cmp: dict, expansions: dict = None) -> bool:
    if expansions is None:
        expansions = {}

    def match_property(n):
        c = cmp.get(n)
        s = src.get(n)
        if isinstance(c, str) and (use_dollar(c).startswith("$")):
            if c in expansions:
                return s == expansions[use_dollar(c)][0]
            else:
                expansions[use_dollar(c)] = [s]
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
            match = PatternMatch(src_nodes[to_do : found_position + 1], found_expansions, patterns)
            found_statements.append(match)
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
    DEFAULT_EXCLUDE_KIND = "comment"

    @staticmethod
    def find_all(
        src_nodes: Sequence[AstProtocol],
        *patterns: Sequence[AstProtocol],
        recursive: bool = True,
    ) -> Sequence[PatternMatch]:
        """
        Finds all pattern matches in the given source nodes.

        Args:
            src_nodes (Sequence[AstProtocol]): The source nodes to search within.
            *patterns (Sequence[AstProtocol]): One or more lists of nodes representing the patterns to match.
            recursive (bool, optional): Whether to search recursively within the source nodes. Defaults to True.

        Returns:
            Sequence[PatternMatch]: A list of pattern matches found in the source nodes.
        """

        return find_all(src_nodes, *patterns, recursive=recursive)

    @staticmethod
    def match_pattern(
        src_nodes: Sequence[AstProtocol],
        patterns: Sequence[AstProtocol],
        recursive=True,
    ) -> Sequence[PatternMatch]:
        """
        Matches a given source node or list of source nodes against a list of pattern nodes.

        Args:
            src_nodes (Sequence[ASTNode] | ASTNode): The source node or list of source nodes to be matched.
            patterns (Sequence[ASTNode]): The list of pattern nodes to match against the source nodes.
            recursive: match children sequence

        Returns:
            Sequence[PatternMatch]: A PatternMatch object if a match is found, otherwise None.
        """
        return match_pattern(src_nodes, patterns, recursive)


# TODO check with pierre whether we should take the highest or the deepest match re implementation backtracking to find the best match
