from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Optional, Sequence

from common import Stream
from .ast_node import ASTNode,MATCH_ALL, MATCH_ONE

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"

def is_match_tree(src:list, cmp:list, expansions={}):
    if cmp == None or src == None:
        return src == cmp
    if not isinstance(src , list) or not isinstance(cmp , list):
        return src == cmp
    if len(cmp) == 0 or len(src) == 0:
        return src == cmp
    if len(cmp) == 1 and isinstance(cmp[0], ASTNode) and cmp[0].kind == MATCH_ALL:
        expansions[cmp[0].name] = src
        return True
    return find_in_list(src, cmp, expansions) + 1 == len(src)

def find_in_list(src:list, cmp:list, exp={}):
    found_position = 0
    greedy = None
    expansion_start = -1
    i = 0
    while i <len(src):
        if found_position >=len(cmp):
            break
        if isinstance(cmp[found_position], ASTNode) and cmp[found_position].kind == MATCH_ALL:
            current_name = cmp[found_position].name
            if current_name in exp:
                end = i + len(exp[current_name])
                if is_match_tree(exp[current_name], src[i:end], {}):
                    found_position += 1
                    i=end
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
    if found_position == len(cmp) - 1 and isinstance(cmp[found_position], ASTNode) and cmp[found_position].kind == MATCH_ALL:
        if cmp[found_position].name in exp:
            if exp[cmp[found_position].name] != []:
                for p in cmp:
                    if isinstance(p, ASTNode) and p.name in exp:
                        exp.pop(p.name)
                return -1
        else:
            exp[cmp[found_position].name] = []
            i=len(src)
    elif found_position == len(cmp):
        if i < len(src) and greedy:
            exp[greedy] = src[expansion_start:]
            i=len(src)
        elif len(cmp) >=2 and isinstance(cmp[-2], ASTNode) and cmp[-2].kind == MATCH_ALL and isinstance(cmp[-1], ASTNode) and cmp[-1].kind ==MATCH_ONE:
            exp[cmp[-2].name] = src[expansion_start:-1]
            exp[cmp[-1].name] = src[-1:]
            i=len(src)
    else:
        return -1
    return i-1
    # do reverse search?


def is_match(src, cmp, expansions={}) -> bool:
    if isinstance(cmp, ASTNode) and cmp.kind == MATCH_ONE and not ( isinstance(src, ASTNode) and src.kind in ['Module', 'FUNCTION_DECL','TRANSLATION_UNIT']):
        if cmp.name in expansions:
            return is_match(src, expansions[cmp.name][0])
        else:
            expansions[cmp.name] = [src]
            return True
    elif isinstance(src, ASTNode) and isinstance(cmp, ASTNode) and (cmp.kind != src.kind or not src.is_part_of_translation_unit()):
        return False
    elif isinstance(cmp, list):
        return is_match_tree(src, cmp, expansions)
    elif isinstance(cmp, dict):
        return is_match_dict(src, cmp, expansions)
    elif isinstance(cmp, str):
        if cmp.startswith('$') or cmp.startswith(MATCH_ONE):
            if cmp in expansions:
                return is_match(src, expansions[cmp.replace(MATCH_ONE,'$')][0])
            else:
                expansions[cmp.replace(MATCH_ONE,'$')] = [src]
                return True
        return src == cmp
    elif isinstance(cmp, int):
        return src == cmp
    elif cmp == None:
        return src == None
    elif isinstance(cmp, ASTNode):
        return (is_match_dict(src.properties, cmp.properties, expansions)
                and is_match_tree(remove_comment_macro(src.children), cmp.children, expansions))
    else:
        return src == cmp


def remove_comment_macro(src: list[ASTNode]) -> list[ASTNode]:
    csrc = []
    for c in src:
        if not c.kind in ['FullComment', 'MACRO_DEFINITION']:
            csrc.append(c)
    return csrc

IRRELEVANT_PROPS=['macro_expansion']
def is_match_dict(src:dict, cmp:dict, expansions:dict) -> bool:
    all_keys = src.keys()|cmp.keys()
    return all(n in IRRELEVANT_PROPS or (n in src and n in cmp and is_match(src[n], cmp[n], expansions)) for n in all_keys)



def exclude_nodes_by_kind(exclude_kind: str, nodes: Sequence[ASTNode]) -> Sequence[ASTNode]:
    if exclude_kind:
        return [
            node
            for node in nodes
            if re.search(exclude_kind, node.kind, re.IGNORECASE) is None
        ]
        # return filter(lambda node: re.search(exclude_kind,node.kind, re.IGNORECASE)==None, nodes)
    return nodes


def exclude_nodes_by_kind_as_sequence(
        exclude_kind: str, nodes: Sequence[ASTNode]
) -> Sequence[ASTNode]:
    return exclude_nodes_by_kind(exclude_kind, nodes)


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
            *patterns_list: Sequence[ASTNode] | ConstrainedPattern,
            recursive: bool = True,
            exclude_kind: str = DEFAULT_EXCLUDE_KIND,
            part_of_translation_unit: bool = True,
    ) -> Stream[PatternMatch]:
        return Stream(
            self._match_referenced_by(
                patterns_list, recursive, exclude_kind, part_of_translation_unit
            )
        )

    def match_references(
            self,
            *patterns_list: Sequence[ASTNode] | ConstrainedPattern,
            recursive: bool = True,
            exclude_kind: str = DEFAULT_EXCLUDE_KIND,
            part_of_translation_unit: bool = True,
    ) -> Stream[PatternMatch]:
        return Stream(
            self._match_references(
                patterns_list, recursive, exclude_kind, part_of_translation_unit
            )
        )

    def _match_referenced_by(
            self,
            patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
            recursive: bool,
            exclude_kind: str,
            part_of_translation_unit: bool,
    ) -> Iterable[PatternMatch]:
        for n in self.src_nodes:
            for ref in n.referenced_by:
                yield from MatchFinder.find_all_strict(
                    ref.node,
                    patterns_list,
                    recursive,
                    exclude_kind,
                    part_of_translation_unit,
                ).to_iterable()

    def _match_references(
            self, patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
            recursive: bool, exclude_kind: str, part_of_translation_unit: bool
    ) -> Iterable[PatternMatch]:
        for n in self.nodes:
            for ref in n.references:
                yield from MatchFinder.find_all_strict(
                    [ref.node],
                    patterns_list,
                    recursive,
                    exclude_kind,
                    part_of_translation_unit,
                ).to_iterable()


# TODO: do we want to merge the filter functionality with the find pattern?
@dataclass(frozen=True)
class ConstrainedPattern:
    patterns: Sequence[ASTNode] | ASTNode  # TODO Why plural, i.e., patterns?
    eligible: Callable[[PatternMatch], bool]


class MatchFinder:
    DEFAULT_EXCLUDE_KIND = "comment"

    @staticmethod
    def find_all(
            src_nodes: Sequence[ASTNode] | ASTNode,
            *patterns_list: Sequence[ASTNode] | ConstrainedPattern,
            recursive: bool = True,
            exclude_kind: str = DEFAULT_EXCLUDE_KIND,
            part_of_translation_unit: bool = True,
    ) -> Stream[PatternMatch]:
        return MatchFinder.find_all_strict(
            src_nodes,
            patterns_list,
            recursive=recursive,
            exclude_kind=exclude_kind,
            part_of_translation_unit=part_of_translation_unit,
        )

    # TODO: Why don't we define types for X | Sequence[X]?
    # TODO: Why don't we enforce that input is always a sequence of ASTNodes (so just use [] around a single ASTNode)?
    # TODO: Why don't we define a type for a pattern: Sequence[ASTNode] | ConstrainedPattern
    # TODO: Why don't we introduce a Pattern class (with multiple constructors for the different cases)?

    # TODO: why is the type of patterns_list different from find_all (directly above)?
    @staticmethod
    def find_all_strict(
            src_nodes: Sequence[ASTNode] | ASTNode,
            patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
            recursive: bool = True,
            exclude_kind: str = DEFAULT_EXCLUDE_KIND,
            part_of_translation_unit: bool = True,
    ) -> Stream[PatternMatch]:
        """
        Finds all pattern matches in the given source nodes.

        Args:
            src_nodes (Sequence[ASTNode] | ASTNode): The source nodes to search within. Can be a single ASTNode or a list of ASTNodes.
            *patterns_list (Sequence[ASTNode]): One or more lists of ASTNodes representing the patterns to match.
            recursive (bool, optional): Whether to search recursively within the source nodes. Defaults to True.
            exclude_kind (type, optional): The kind of nodes to exclude from the search. Defaults to DEFAULT_EXCLUDE_KIND.

        Returns:
            Stream[PatternMatch]: A stream of pattern matches found in the source nodes.
        """
        if not isinstance(src_nodes, Sequence):
            src_nodes = [src_nodes]

        def src_filter(nodes: Sequence[ASTNode]):
            if not part_of_translation_unit:
                return exclude_nodes_by_kind(exclude_kind, nodes)
            return [
                node
                for node in exclude_nodes_by_kind_as_sequence(
                    exclude_kind, nodes
                )
                if node.is_part_of_translation_unit()
            ]

        return Stream(
            MatchFinder.__find_all(
                src_nodes, patterns_list, recursive=recursive, src_filter=src_filter
            )
        )

    @staticmethod
    def match_pattern(
            src_nodes: [ASTNode] | ASTNode,
            patterns: [ASTNode] | ConstrainedPattern,
            src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]] = lambda n: n,
    ) -> [PatternMatch]:
        """
        Matches a given source node or list of source nodes against a list of pattern nodes.

        Args:
            src_nodes (Sequence[ASTNode] | ASTNode): The source node or list of source nodes to be matched.
            patterns (Sequence[ASTNode]): The list of pattern nodes to match against the source nodes.
            src_filter: The kind of nodes to exclude from matching.

        Returns:
            Optional[PatternMatch]: A PatternMatch object if a match is found, otherwise None.
        """
        eligible: Callable[[PatternMatch], bool] = lambda _: True
        if isinstance(src_nodes, ASTNode):
            src_nodes = [src_nodes]
        if isinstance(patterns, ConstrainedPattern):
            eligible = patterns.eligible
            patterns = (
                patterns.patterns
                if isinstance(patterns.patterns, Sequence)
                else [patterns.patterns]
            )
        if isinstance(patterns, ASTNode):
            patterns = [patterns]

        patterns = src_filter(patterns)  # exclude nodes by kind
        keys = []
        multiplicity = {key: 0 for key, count in Counter(keys).items() if count > 1}
        return MatchFinder.__match_pattern(src_nodes, patterns, 0, multiplicity, None, src_filter=src_filter)

    @staticmethod
    def __find_all(
            src_nodes: Sequence[ASTNode],
            patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
            recursive: bool,
            src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]],
    ) -> Iterator[PatternMatch]:
        found_matches = []
        for patterns in patterns_list:
            found_matches.extend(MatchFinder.match_pattern(src_nodes, patterns))
        return found_matches

        # src_nodes = src_filter(
        #     src_nodes
        # )  # exclude nodes by kind and optionally is part of translation unit

    @staticmethod
    def __match_pattern(
            src_nodes: Sequence[ASTNode],
            patterns: Sequence[ASTNode],
            depth: int,
            multiplicity: dict[str, int],
            pattern_match: Optional[PatternMatch],
            src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]],
    ) -> Sequence[PatternMatch]:
        found_statements = []
        to_do = src_nodes
        while len(to_do)>0:
            found_expansions = {}
            found_position  = find_in_list(to_do, patterns, found_expansions)
            if found_position >=0:
                match = PatternMatch(to_do[:found_position+1], found_expansions, patterns)
                found_statements.append(match)
                to_do = to_do[found_position+1:]
            else:
                if to_do[0].children:
                    found_statements.extend(MatchFinder.__match_pattern(
                        remove_comment_macro(to_do[0].children),
                        patterns,
                        depth,
                        multiplicity,
                        pattern_match,
                        src_filter,
                    ))
                to_do = to_do[1:]


        return found_statements

        # TODO check with pierre whether we should take the highest or the deepest match

def do_log(indent: int, *msgs: str):
    text = "\n".join(msgs)
    print(" ".join(f'{" " * indent}{l}' for l in text.splitlines()))


def raw(nodes: Sequence[ASTNode]):
    return " ".join([n.text for n in nodes])
