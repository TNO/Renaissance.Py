from typing import Sequence, Self, Iterable, Protocol, runtime_checkable

from .ast_node import ASTNode
from common import Stream
from impl import MATCH_ALL, MATCH_ONE

VERBOSE = False


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
        self._remaining_nodes: list[ASTNode] = []

    def __str__(self):
        res = ''
        for node in self.nodes:
            res += node.signature
        return res

    def get_raw_signatures(self):
        return str(self)

    def match_referenced_by(
            self,
            patterns: Sequence[ASTNode],
            recursive: bool = True) -> Stream[Self]:
        found_matches = []
        for node in self.nodes:
            for ref in node.referenced_by:
                for pattern in patterns:
                    found_matches.extend(MatchFinder.match_pattern([ref.node], pattern, recursive))
        return Stream(found_matches)

    def match_references(
            self,
            patterns: Iterable[ASTNode],
            recursive: bool = True) -> Stream[Self]:
        found_matches = []
        for node in self.nodes:
            for ref in node.references:
                for pattern in patterns:
                    found_matches.extend(MatchFinder.match_pattern([ref.node], pattern, recursive))
        return Stream(found_matches)


def is_match_tree(src: Sequence, cmp: Sequence, expansions=None):
    if expansions is None:
        expansions = {}
    if not cmp or not src:
        return src == cmp
    if not isinstance(src, list) or not isinstance(cmp, list):
        return src == cmp
    if len(cmp) == 0 or len(src) == 0:
        return src == cmp
    if len(cmp) == 1 and isinstance(cmp[0], ASTNode) and cmp[0].kind == MATCH_ALL:
        expansions[cmp[0].name] = src
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
        if getattr(cmp[found_position], 'kind', 'unknown') == MATCH_ALL:
            current_name = getattr(cmp[found_position], 'name', 'unknown')
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
    if found_position == len(cmp) - 1 and isinstance(cmp[found_position], ASTNode) and cmp[
        found_position].kind == MATCH_ALL:
        if cmp[found_position].name in exp:
            if exp[cmp[found_position].name]:
                for p in cmp:
                    if isinstance(p, ASTNode) and p.name in exp:
                        exp.pop(p.name)
                return -1
        else:
            exp[cmp[found_position].name] = []
            i = len(src)
    elif found_position == len(cmp):
        if i < len(src) and greedy:
            exp[greedy] = src[expansion_start:]
            i = len(src)
        elif len(cmp) >= 2 and isinstance(cmp[-2], ASTNode) and cmp[-2].kind == MATCH_ALL and isinstance(cmp[-1],
                                                                                                         ASTNode) and \
                cmp[-1].kind == MATCH_ONE:
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
    if src.kind not in ['Module', 'TRANSLATION_UNIT'] and cmp.kind == MATCH_ONE and cmp.name:
        if cmp.name in expansions:
            return is_match(src, expansions[cmp.name][0])
        else:
            expansions[cmp.name] = [src]
            return True
    elif cmp.kind != src.kind:
        return False
    elif isinstance(src, list) and isinstance(cmp, list):
        return is_match_tree(src, cmp, expansions)
    elif isinstance(src, dict) and isinstance(cmp, dict):
        return is_match_dict(src, cmp, expansions)
    elif isinstance(cmp, str):
        if cmp.startswith('$') or cmp.startswith(MATCH_ONE):
            if cmp in expansions:
                return is_match(src, expansions[cmp.replace(MATCH_ONE, '$')][0])
            else:
                expansions[cmp.replace(MATCH_ONE, '$')] = [src]
                return True
        return src == cmp
    elif isinstance(src, AstProtocol) and isinstance(cmp, AstProtocol):
        return (is_match_dict(src.properties, cmp.properties, expansions)
                and is_match_tree(exclude_nodes_by_kind(src.children), cmp.children, expansions))
    else:
        return src == cmp


DEFAULT_EXCLUDE_KIND = {'FullComment', 'MACRO_DEFINITION'}


def exclude_nodes_by_kind(src: list[ASTNode]) -> list[ASTNode]:
    return [c for c in src if c.kind not in DEFAULT_EXCLUDE_KIND]


IRRELEVANT_PROPS = {'macro_expansion', 'start_point', 'end_point'}


def is_match_dict(src: dict, cmp: dict, expansions: dict) -> bool:
    def match_property(n):
        c = cmp.get(n)
        s = src.get(n)
        if isinstance(c, str) and (c.startswith('$') or c.startswith(MATCH_ONE)):
            if c in expansions:
                return s == expansions[c][0]
            else:
                expansions[c] = [s]
                return True
        return s == c
    all_keys = (src.keys() | cmp.keys()) - IRRELEVANT_PROPS
    return all(match_property(n)  for n in all_keys)


def match_pattern(src_nodes: Sequence[ASTNode], patterns: Sequence[ASTNode], recursive=True) -> Sequence[PatternMatch]:
    """
    Matches a given source node or list of source nodes against a list of pattern nodes.

    Args:
        src_nodes (Sequence[ASTNode] | ASTNode): The source node or list of source nodes to be matched.
        patterns (Sequence[ASTNode]): The list of pattern nodes to match against the source nodes.
        recursive: match children sequence

    Returns:
        Sequence[PatternMatch]: A PatternMatch object if a match is found, otherwise None.
    """
    found_statements = []
    to_do = src_nodes
    while len(to_do) > 0:
        found_expansions = {}
        found_position = find_in_list(to_do, patterns, found_expansions)
        if found_position >= 0:
            match = PatternMatch(to_do[:found_position + 1], found_expansions, patterns)
            found_statements.append(match)
            to_do = to_do[found_position + 1:]
        else:
            if recursive:
                found_statements.extend(
                    MatchFinder.match_pattern(exclude_nodes_by_kind(getattr(to_do[0], 'children', [])), patterns,
                                              recursive))
            to_do = to_do[1:]

    return found_statements


class MatchFinder:
    DEFAULT_EXCLUDE_KIND = "comment"

    @staticmethod
    def find_all(
            src_nodes: Sequence[ASTNode],
            *patterns: Sequence[ASTNode],
            recursive: bool = True,
    ) -> Stream[PatternMatch]:
        """
        Finds all pattern matches in the given source nodes.

        Args:
            src_nodes (Sequence[ASTNode] | ASTNode): The source nodes to search within. Can be a single ASTNode or a list of ASTNodes.
            *patterns (Sequence[ASTNode]): One or more lists of ASTNodes representing the patterns to match.
            recursive (bool, optional): Whether to search recursively within the source nodes. Defaults to True.

        Returns:
            Stream[PatternMatch]: A stream of pattern matches found in the source nodes.
        """
        found_matches = []
        for pattern in patterns:
            found_matches.extend(MatchFinder.match_pattern(src_nodes, pattern, recursive))
        return Stream(found_matches)

    @staticmethod
    def match_pattern(src_nodes: Sequence[ASTNode], patterns: Sequence[ASTNode], recursive=True) -> Sequence[
        PatternMatch]:
        return match_pattern(src_nodes, patterns, recursive)

# TODO check with pierre whether we should take the highest or the deepest match re imple backtracking to find the best match
