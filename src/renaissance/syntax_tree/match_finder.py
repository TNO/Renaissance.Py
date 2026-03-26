from typing import Sequence, Self, Iterable, Protocol, runtime_checkable

from more_itertools import flatten

from renaissance.impl import MATCH_ALL, MATCH_ONE
from ..utils.node_util import use_dollar



IRRELEVANT_PROPS = {"macro_expansion", "start_point", "end_point", "source_code"}
DEFAULT_EXCLUDE_KIND = {"FullComment", "MACRO_DEFINITION"}


@runtime_checkable
class AstProtocol(Protocol):
    kind: str
    properties: dict
    children: list[Self]
    signature: str
    name: str


class PatternMatch:
    def __init__(self, nodes, expansions, patterns):
        self.nodes = nodes
        self.expansions = expansions
        self.patterns = patterns
        self._remaining_nodes: list[AstProtocol] = []

    def __str__(self):
        return "\n".join(node.signature for node in self.nodes)
    @property
    def signature(self):
        return str(self)

    def __getitem__(self, key):
        return "\n".join( node.signature  if isinstance(node, AstProtocol) else node for node in self.expansions[key])
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
    return find_in_list(src, cmp, expansions) + 1 == len(src)


def find_in_list(src: Sequence, cmp: Sequence, exp=None):
    if exp is None:
        exp = {}
    found_position = 0
    greedy = None
    expansion_start = -1
    i = 0
    while i < len(src):
        if found_position >= len(cmp):
            break
        if getattr(cmp[found_position], "kind", "unknown") == MATCH_ALL:
            current_name = getattr(cmp[found_position], "name", "unknown")
            if current_name in exp:
                end = i + len(exp[current_name])
                if is_match_tree(exp[current_name], src[i:end], {}):
                    found_position += 1
                    i = end
                else:
                    return -1
            else:
                greedy = cmp[found_position].name
                expansion_start = i
                found_position += 1
        elif is_match(src[i], cmp[found_position], exp):
            if greedy:
                exp[greedy] = src[expansion_start:i]
                greedy = None
            found_position += 1
            i += 1
        elif greedy:
            i += 1
        else:
            return -1
    if found_position == len(cmp) - 1 and isinstance(cmp[found_position], AstProtocol) and cmp[found_position].kind == MATCH_ALL:
        if cmp[found_position].name in exp:
            if exp[cmp[found_position].name]:
                for p in cmp:
                    if isinstance(p, AstProtocol) and p.name in exp:
                        exp.pop(p.name)
                return -1
        else:
            exp[cmp[found_position].name] = []
            i = len(src)
    elif found_position == len(cmp):
        if i < len(src) and greedy:
            exp[greedy] = src[expansion_start:]
            i = len(src)
        elif (
            len(cmp) >= 2
            and isinstance(cmp[-2], AstProtocol)
            and cmp[-2].kind == MATCH_ALL
            and isinstance(cmp[-1], AstProtocol)
            and cmp[-1].kind == MATCH_ONE
        ):
            exp[cmp[-2].name] = src[expansion_start:-1]
            exp[cmp[-1].name] = src[-1:]
            i = len(src)
    else:
        return -1
    return i - 1
    # do reverse search?


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
    to_do = src_nodes
    while len(to_do) > 0:
        found_expansions = {}
        found_position = find_in_list(to_do, patterns, found_expansions)
        if found_position >= 0:
            match = PatternMatch(to_do[: found_position + 1], found_expansions, patterns)
            found_statements.append(match)
            to_do = to_do[found_position + 1 :]
        else:
            if recursive:
                found_statements.extend(
                    MatchFinder.match_pattern(
                        exclude_nodes_by_kind(getattr(to_do[0], "children", [])),
                        patterns,
                        recursive,
                    )
                )
            to_do = to_do[1:]

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
