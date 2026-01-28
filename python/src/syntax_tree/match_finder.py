from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cache
import re
import sys
from typing import Callable, Iterable, Iterator, Optional, Sequence

from coverage.misc import isolate_module

from common import Stream
from collections import Counter

from .ast_node import ASTNode, ASTReference

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"
MATCH_ONE = '_MatchOne__'
MATCH_ALL = '_MatchAll__'

def is_match(src, cmp,expansion={}) -> bool:
    if isinstance(cmp, ASTNode) and cmp.kind==MATCH_ONE and not src.kind=='Module':
        if cmp.name in expansion:
            return is_match(src,expansion[cmp.name][0])
        else:
            expansion[cmp.name]=[src]
            return True
    elif isinstance(src, ASTNode) and cmp.kind !=src.kind:
        return False
    elif isinstance(cmp, list):
        match = True
        if len(cmp) > len(src):
            return False
        for i in range(len(src)):
            if len(cmp)==1 and cmp[0].kind==MATCH_ALL:
                expansion[cmp[0].name] = src
                return True
            elif i >= len(cmp):
                return False
            match &= is_match(src[i], cmp[i],expansion)
        return match
    elif isinstance(cmp, dict):
        for n in cmp:
            if n not in src or not is_match(src[n], cmp[n],expansion):
                return False
        return True
    elif isinstance(cmp, str):
        return src == cmp
    elif isinstance(cmp, int):
        return src == cmp
    elif cmp ==None:
        return src == None
    elif isinstance(cmp, ASTNode):
        return ( is_match(src.expression, cmp.expression,expansion)
                and is_match(src.name, cmp.name, expansion)
                and is_match(src.properties, cmp.properties,expansion)
                and is_match(src.children, cmp.children,expansion))
    else:
        src==cmp

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
            res += node.get_raw_signature()
        return res
    def get_raw_signatures(self):
        return str(self)


    def match_referenced_by(
        self,
        *patterns_list: Sequence[ASTNode]|ConstrainedPattern,
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
        *patterns_list: Sequence[ASTNode]|ConstrainedPattern,
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
        patterns_list: Sequence[Sequence[ASTNode]|ConstrainedPattern],
        recursive: bool,
        exclude_kind: str,
        part_of_translation_unit: bool,
    ) -> Iterable[PatternMatch]:
        for n in self.src_nodes:
            for ref in n.referenced_by:
                yield from MatchFinder.find_all_strict(
                    ref.get_node(),
                    patterns_list,
                    recursive,
                    exclude_kind,
                    part_of_translation_unit,
                ).to_iterable()

    def _match_references(
        self, patterns_list : Sequence[Sequence[ASTNode]|ConstrainedPattern], 
        recursive: bool, exclude_kind: str, part_of_translation_unit: bool
    ) -> Iterable[PatternMatch]:
        for n in self.src_nodes:
            for ref in n.references:
                yield from MatchFinder.find_all_strict(
                    [ref.get_node()],
                    patterns_list,
                    recursive,
                    exclude_kind,
                    part_of_translation_unit,
                ).to_iterable()



#TODO: do we want to merge the filter functionality with the find pattern?
@dataclass(frozen=True)
class ConstrainedPattern:
    patterns: Sequence[ASTNode] | ASTNode       # TODO Why plural, i.e., patterns?
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

    #TODO: Why don't we define types for X | Sequence[X]?
    #TODO: Why don't we enforce that input is always a sequence of ASTNodes (so just use [] around a single ASTNode)?
    #TODO: Why don't we define a type for a pattern: Sequence[ASTNode] | ConstrainedPattern
    #TODO: Why don't we introduce a Pattern class (with multiple constructors for the different cases)?

    #TODO: why is the type of patterns_list different from find_all (directly above)?
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
        src_nodes: Sequence[ASTNode] | ASTNode,
        patterns: Sequence[ASTNode] | ConstrainedPattern,
        src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]] = lambda n: n,
    ) -> Sequence[PatternMatch]:
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
            found_matches.extend(MatchFinder.match_pattern(src_nodes,patterns))
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
        greedy = False
        foundPosition = 0
        foundPositionInExpandedList = 0
        expansions = {}
        foundStatements =[]

        # this case does not really make sense
        if len(patterns) ==1 and patterns[0].kind ==MATCH_ALL:
            foundStatements.append(src_nodes)
            return foundStatements
        if not patterns or len(patterns) ==0:
            return foundStatements

        for i in range(len(src_nodes)):
            node = src_nodes[i]
            pattern = patterns[foundPosition]
            if pattern.kind == MATCH_ALL:
                current_name = patterns[foundPosition].name
                if current_name in expansions:
                    if is_match(expansions[current_name][foundPositionInExpandedList], node):
                        foundPositionInExpandedList = foundPositionInExpandedList + 1
                        if (foundPositionInExpandedList == len(expansions[current_name])):
                            # found all match
                            foundPositionInExpandedList = 0
                            foundPosition += 1
                    else:
                        foundPosition = 0
                else:
                    greedy = True
                    foundPosition += 1
                    pattern = patterns[foundPosition]
                    expansion_start = i
                    foundPositionInExpandedList = 0
            if is_match(node, pattern, expansions):
                if foundPosition == 0:
                    start = i
                if greedy == True:
                    greedy = False
                    last_name = patterns[foundPosition - 1].name
                    if not last_name in expansions:
                        expansions[last_name] = src_nodes[expansion_start:i]
                        foundPositionInExpandedList = 0
                foundPosition += 1
                if foundPosition == len(patterns):
                    end = i + 1
                    # pattern_match._query_create(MatchUtils.EXACT_MATCH)

                    foundStatements.append(PatternMatch(src_nodes[start:end], expansions, patterns))
                    expansions={}
                    foundPosition = 0
            else:
                if node.expression and len(patterns) == 1:
                    foundStatements.extend(MatchFinder.__match_pattern(
                        [node.expression],
                        patterns,
                        depth,
                        multiplicity,
                        pattern_match,
                        src_filter,
                    ))
                if node.children:
                    foundStatements.extend(MatchFinder.__match_pattern(
                        node.children,
                        patterns,
                        depth,
                        multiplicity,
                        pattern_match,
                        src_filter,
                    ))
                if node.orelse:
                    foundStatements.extend(MatchFinder.__match_pattern(
                        node.orelse,
                        patterns,
                        depth,
                        multiplicity,
                        pattern_match,
                        src_filter,
                    ))

        return foundStatements

        #             # TODO check with pierre whether we should take the highest or the deepest match


# class MatchValidation:
#     @staticmethod
#     def _check_duplicate_matches(key_matches: Sequence[KeyMatch]):
#         """
#         Checks for duplicate matches in the keyMatches attribute.
#
#         This method groups the keyMatches by their keys and identifies groups with the same key.
#         It then transposes the nodes in these groups to compare nodes at the same index across different groups.
#         If any group of nodes at the same index do not match, the method returns False.
#
#         Returns:
#             bool: False if any group of nodes at the same index do not match, otherwise None.
#         """
#         key_groups: dict[str, list[list[ASTNode]]] = {}
#         for key_match in [m for m in key_matches if MatchUtils.is_wildcard(m.key)]:
#             if key_match.key not in key_groups:
#                 key_groups[key_match.key] = []
#             # for single wildcards only the last/deepest node is relevant
#             # an example of this is CallExpr where is matches twice once for the function and once for the function name
#             # only the function name must be evaluated
#             nodes = (
#                 key_match.nodes
#                 if MatchUtils.is_multi_wildcard(key_match.key)
#                 else key_match.nodes[-1:]
#             )
#             key_groups[key_match.key].append(nodes)
#         for key, same in key_groups.items():
#             if len(same) < 2:
#                 continue
#             # cmp
#             comp = same[0]
#             for row in same[1:]:
#                 if len(comp) != len(row):
#                     if VERBOSE:
#                         do_log(
#                             0,
#                             "FAILED on duplicate matches having different lengths",
#                             key,
#                             f"first[{raw(comp)}]",
#                             f" next[{raw(row)}]",
#                         )
#                     return False
#                 for col_idx, node in enumerate(row):
#                     if not MatchFinder.is_match(comp[col_idx : col_idx + 1], [node]):
#                         if VERBOSE:
#                             do_log(
#                                 0,
#                                 "FAILED on duplicate matches not matching",
#                                 key,
#                                 " != ".join(
#                                     ["[" + raw(comp) + "]", "[" + raw(row) + "]"]
#                                 ),
#                             )
#                         return False
#         return True
#
#     @staticmethod
#     def _check_single_matches(key_matches: Sequence[KeyMatch]):
#         """
#         Checks for single matches in the keyMatches attribute.
#
#         This method checks if any keyMatch has exactly  one node. If not the method returns False.
#
#         Returns:
#             bool: False if any keyMatch has more than one node, otherwise None.
#         """
#         result = all(
#             len(key_match.nodes) > 0
#             for key_match in key_matches
#             if MatchUtils.is_single_wildcard(key_match.key)
#         )
#         if not result and VERBOSE:
#             print(f"FAILED on single match")
#         return result
#
#     @staticmethod
#     def validate(key_matches: Sequence[KeyMatch]):
#         return MatchValidation._check_single_matches(
#             key_matches
#         ) and MatchValidation._check_duplicate_matches(key_matches)
#

def do_log(indent: int, *msgs: str):
    text = "\n".join(msgs)
    print(" ".join(f'{" "*indent}{l}' for l in text.splitlines()))


def raw(nodes: Sequence[ASTNode]):
    return " ".join([n.text for n in nodes])

