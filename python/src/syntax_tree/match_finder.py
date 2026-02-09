from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Optional, Sequence

from common import Stream
from .ast_node import ASTNode,MATCH_ALL, MATCH_ONE

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"


def is_match_tree(src, cmp, expansions={}):
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

def find_in_list(src, cmp, exp={}):
    foundPosition = 0
    greedy = False
    # src = remove_comment_macro(src)
    i = 0
    while i <len(src):
        pattern = cmp[foundPosition]
        if isinstance(pattern, ASTNode) and pattern.kind == MATCH_ALL:
            current_name = pattern.name
            if current_name in exp:
                end = i + len(exp[current_name])
                if is_match_tree(exp[current_name], src[i:end], {}):
                    foundPosition += 1
                    if foundPosition == len(cmp):
                        return end - 1
                    else:
                        pattern = cmp[foundPosition]
                        i=end
                        expansion_start = i

                else:
                    exp.pop(current_name)
                    foundPosition = 0
                    return False
            else:
                greedy = True
                foundPosition += 1
                if foundPosition == len(cmp):
                    exp[current_name] = src[i:]
                    return len(src) - 1
                else:
                    pattern = cmp[foundPosition]
                    expansion_start = i

        if is_match(src[i], pattern, exp):
            if greedy == True:
                greedy = False
                last_name = cmp[foundPosition - 1].name
                if not last_name in exp:
                    if (not isinstance(pattern, ASTNode)) or pattern.kind != MATCH_ONE:
                        exp[last_name] = src[expansion_start:i]
                    else:
                        if foundPosition + 1 == len(cmp):
                            current_name = cmp[foundPosition].name
                            end = len(src) - 1
                            exp[last_name] = src[expansion_start:end]
                            exp[current_name] = src[end:]
                            return end
            foundPosition += 1
            if foundPosition == len(cmp):
                return i
        elif not greedy:
            return -1
        i+=1
    if foundPosition < len(cmp):
        if foundPosition == len(cmp) - 1 and isinstance(cmp[foundPosition], ASTNode) and cmp[
            foundPosition].kind == MATCH_ALL:
            if cmp[foundPosition].name in exp:
                return exp[cmp[foundPosition].name] == []
            else:
                exp[cmp[foundPosition].name] = []
                return i-1
        for p in cmp:
            if isinstance(p, ASTNode) and p.name in exp:
                exp.pop(p.name)
        return -1
    return i-1


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
        return (is_match_dict(src.properties, cmp.properties, {})
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
def is_match_dict(src, cmp, expansions) -> bool:
    for n in cmp:
        if n in IRRELEVANT_PROPS:
            continue
        else:
            if n not in src or not is_match(src[n], cmp[n], expansions):
                return False
    return True


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
    print(" ".join(f'{" " * indent}{l}' for l in text.splitlines()))


def raw(nodes: Sequence[ASTNode]):
    return " ".join([n.text for n in nodes])
