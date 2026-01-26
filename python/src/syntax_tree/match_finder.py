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

from impl.python import MATCH_ONE
from impl.python.python_ast_node import MATCH_ALL
from .ast_node import ASTNode, ASTReference

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"

expandArgList = {}
expansionList = {}
expansion = {}
foundStatements = []
def reset_expansions():
    expansion.clear()
    expansionList.clear()
    foundStatements.clear()

class MatchUtils:

    EXACT_MATCH = "EXACT_MATCH"

    @staticmethod
    def is_match(src, cmp) -> bool:
        if isinstance(cmp, ASTNode) and cmp.kind==MATCH_ONE and not src.kind=='Module':
            expansion[cmp]=src
            return True
        elif isinstance(src, ASTNode) and cmp.kind !=src.kind:
            return False
        elif isinstance(cmp, list):
            match = True
            if len(cmp) > len(src):
                return False
            for i in range(len(src)):
                if i >= len(cmp):
                    return False
                match &= MatchUtils.is_match(src[i], cmp[i])
            return match
        elif isinstance(cmp, dict):
            for n in cmp:
                if n not in src or not MatchUtils.is_match(src[n], cmp[n]):
                    return False
            return True
        elif isinstance(cmp, str):
            return src == cmp
        elif isinstance(cmp, int):
            return src == cmp
        elif cmp ==None:
            return src == None
        else:
            return (MatchUtils.is_match(src.expression, cmp.expression)
                    and MatchUtils.is_match(src.properties, cmp.properties)
                    and MatchUtils.is_match(src.children, cmp.children))

    @staticmethod
    def is_wildcard(target: ASTNode | str, multiplicity=None) -> bool:
        if (target == None):
            return False
        if isinstance(target, ASTNode) and (target.get_kind() == 'Name' or type(target.node.value) == ast.Name):
            target = target.get_name()
        if not isinstance(target, str):
            return False
        if(multiplicity=='single'):
            second  = len(target)==1 or target[1] != '$'
        if (multiplicity == 'multi'):
            second = len(target)>1 and target[1] == '$'
        else:
            second = True
        return target[0]=='$' and second

    @staticmethod
    def is_multi_wildcard(target: ASTNode | str) -> bool:
        MatchUtils.is_wildcard(target, 'multi')

    @staticmethod
    def is_single_wildcard(target: ASTNode | str) -> bool:
        return  MatchUtils.is_wildcard(target, 'single')

    @staticmethod
    def exclude_nodes_by_kind(
        exclude_kind: str, nodes: Sequence[ASTNode]
    ) -> Sequence[ASTNode]:
        if exclude_kind:
            return [
                node
                for node in nodes
                if re.search(exclude_kind, node.get_kind(), re.IGNORECASE) is None
            ]
            # return filter(lambda node: re.search(exclude_kind,node.get_kind(), re.IGNORECASE)==None, nodes)
        return nodes

    @staticmethod
    def exclude_nodes_by_kind_as_sequence(
        exclude_kind: str, nodes: Sequence[ASTNode]
    ) -> Sequence[ASTNode]:
        return MatchUtils.exclude_nodes_by_kind(exclude_kind, nodes)


    @staticmethod
    def get_multi_wildcard_keys(
        patterns: Sequence[ASTNode], result: list[str] = []
            # TODO: replace mutable default argument
    ) -> list[str]:
        """
        Recursively finds and returns the names of all multi-wildcard patterns in the given list of AST nodes.

        Args:
            patterns (Sequence[ASTNode]): A list of ASTNode objects to search for multi-wildcard patterns.
            result (list, optional): A list to store the names of the multi-wildcard patterns found. Defaults to an empty list.

        Returns:
            list: A list containing the names of all multi-wildcard patterns found in the input list.
        """
        for pattern in patterns:
            if pattern.kind == MATCH_ALL:
                result.append(pattern.get_name())
            MatchUtils.get_multi_wildcard_keys(pattern.get_children(), result)
        return result

    @staticmethod
    def next_multiplicity(multiplicity: dict[str, int]):
        """
        Increments the value of the first key in the dictionary `multiplicity` that has a value less than 3.

        Args:
            multiplicity (dict[str, int]): A dictionary where keys are strings and values are integers.

        Returns:
            bool: True if a value was incremented, False if all values are 3 or greater.
        """
        for k, v in multiplicity.items():
            if v < 3:
                multiplicity[k] += 1
                return True
        return False


class KeyMatch:
    def clone(self) -> KeyMatch:
        cloned = KeyMatch(self.key)
        cloned.nodes = self.nodes[:]
        return cloned

    def __init__(self, key: str) -> None:
        self.key = key
        self.nodes: list[ASTNode] = []

    def _add_node(self, node: ASTNode):
        self.nodes.append(node)


class PatternMatch:
    def __init__(
        self, src_nodes: Sequence[ASTNode], patterns: Sequence[ASTNode]
    ) -> None:
        self._key_matches: list[KeyMatch] = []
        self._remaining_nodes: list[ASTNode] = []
        self.src_nodes: Sequence[ASTNode] = src_nodes
        self.patterns = patterns

    def clone(self) -> PatternMatch:
        # create a new instance of the pattern match
        clone = PatternMatch(self.src_nodes, self.patterns)
        # clone the key matches
        clone._key_matches = [keyMatch.clone() for keyMatch in self._key_matches]
        clone._remaining_nodes = self._remaining_nodes[:]
        return clone

    def _query_create(self, key: str) -> KeyMatch:
        if self._key_matches and self._key_matches[-1].key == key:
            return self._key_matches[-1]
        self._key_matches.append(KeyMatch(key))
        return self._key_matches[-1]

    def _get_remaining_nodes(self) -> Sequence[ASTNode]:
        return self._remaining_nodes

    def _set_remaining_nodes(self, nodes: Sequence[ASTNode]):
        self._remaining_nodes = list(nodes)

    @cache
    def get_nodes(self) -> dict[str, Sequence[ASTNode]]:
        # take the deepest found match for each wildcard key
        return {
            key_match.key: (
                [key_match.nodes[-1]]       #TODO: What other nodes are in the key_match? Why is this needed?
                if MatchUtils.is_single_wildcard(key_match.key)
                else key_match.nodes
            )
            for key_match in self._key_matches
            if MatchUtils.is_wildcard(key_match.key)
        }

    @cache
    def get_raw_signatures(self) -> dict[str, str]:
        nodes = self.get_nodes()

        def get_raw_signature(key: str, location: tuple[int, int]) -> str:
            matched_nodes = nodes.get(key, [])
            if not matched_nodes or location[1] == 0:
                return ""
            return (
                matched_nodes[0]
                .root.get_binary_file_content()[
                    matched_nodes[0]
                    .get_start_offset() : matched_nodes[-1]
                    .get_end_offset()
                ]
                .decode(sys.getfilesystemencoding())
            )

        return {k: get_raw_signature(k, v) for k, v in self.get_locations().items()}

    @cache
    def get_names(self) -> dict[str, list[str]]:
        return {k: [vi.get_name() for vi in v] for k, v in self.get_nodes().items()}

    @cache
    def get_locations(self) -> dict[str, tuple[int, int]]:
        result: dict[str, tuple[int, int]] = {}
        location = 0
        length = 0
        for key_match in self._key_matches:
            # take the first node of the key match or the last location + length if the preceding match does not have a node
            location = (
                key_match.nodes[-1].get_start_offset()
                if key_match.nodes
                else location + length
            )
            length = key_match.nodes[-1].get_length() if key_match.nodes else 0
            if MatchUtils.is_wildcard(key_match.key):
                result[key_match.key] = (location, length)
        return result

    # utilities methods
    def get_name(self, key: str) -> str:
        result = self.get_names().get(key, [])
        assert len(result) == 1, f"Only one name is expected for key {key}"
        return result[0]

    def get_text(self, key: str) -> str:
        result = self.get_nodes().get(key, [])
        assert len(result) == 1, f"Only one node is expected for key {key}"
        return result[0].get_text()

    def get_as_int(self, key: str) -> int:
        return int(self.get_text(key))

    def get_as_float(self, key: str) -> float:
        return float(self.get_text(key))

    def get_references(self) -> Sequence[ASTReference]:
        return [ref for n in self.src_nodes for ref in n.get_references()]

    def get_referenced_by(self) -> Sequence[ASTReference]:
        return [ref for n in self.src_nodes for ref in n.get_referenced_by()]

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
            for ref in n.get_referenced_by():
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
            for ref in n.get_references():
                yield from MatchFinder.find_all_strict(
                    [ref.get_node()],
                    patterns_list,
                    recursive,
                    exclude_kind,
                    part_of_translation_unit,
                ).to_iterable()

    @staticmethod
    def is_multi(placeholder: str):
        return MatchUtils.is_multi_wildcard(placeholder)


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
                return MatchUtils.exclude_nodes_by_kind(exclude_kind, nodes)
            return [
                node
                for node in MatchUtils.exclude_nodes_by_kind_as_sequence(
                    exclude_kind, nodes
                )
                if node.is_part_of_translation_unit()
            ]
        reset_expansions()
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
    ) -> Optional[PatternMatch]:
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
        reset_expansions()
        patterns = src_filter(patterns)  # exclude nodes by kind
        keys = MatchUtils.get_multi_wildcard_keys(patterns)
        multiplicity = {key: 0 for key, count in Counter(keys).items() if count > 1}
        MatchFinder.__match_pattern(src_nodes, patterns, 0, multiplicity, None, src_filter=src_filter)

        return foundStatements
        # patterns = src_filter(patterns)  # exclude nodes by kind
        # keys = MatchUtils.get_multi_wildcard_keys(patterns)
        # multiplicity = {key: 0 for key, count in Counter(keys).items() if count > 1}
        # # remove the last item from multiplicity because it the last item is already greedy
        # if len(multiplicity) > 1:
        #     multiplicity.popitem()
        # has_next_multiplicity = True
        # while has_next_multiplicity:
        #     pattern_match = MatchFinder.__match_pattern(
        #         src_nodes, patterns, 0, multiplicity, None, src_filter=src_filter
        #     )
        #     if pattern_match and eligible(pattern_match):
        #         return pattern_match
        #     has_next_multiplicity = MatchUtils.next_multiplicity(multiplicity)
        # return None

    @staticmethod
    def is_match(
        src1: ASTNode | Sequence[ASTNode],
        src2: ASTNode | Sequence[ASTNode],
        src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]] = lambda n: n,
    ) -> bool:
        if isinstance(src2, ASTNode):
            src2 = [src2]
        return MatchFinder.match_pattern(src1, src2, src_filter=src_filter) is not None

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
        return foundStatements

        # src_nodes = src_filter(
        #     src_nodes
        # )  # exclude nodes by kind and optionally is part of translation unit
        # target_nodes = src_nodes
        #
        # while target_nodes:
        #     pattern_match = None
        #     for patterns in patterns_list:
        #         pattern_match = MatchFinder.match_pattern(
        #             target_nodes, patterns, src_filter
        #         )
        #         if pattern_match:
        #             break  # only one match is needed
        #
        #     if pattern_match:
        #         target_nodes = pattern_match._get_remaining_nodes()
        #         if VERBOSE:
        #             do_log(0, "VALID MATCH FOUND")
        #         yield pattern_match
        #     else:
        #         target_nodes = target_nodes[1:]  # skip the first node
        # # recursively evaluate all children
        # if recursive:
        #     for node in src_nodes:
        #         children = node.get_children()
        #         if children:
        #             yield from MatchFinder.__find_all(
        #                 children,
        #                 patterns_list,
        #                 recursive=recursive,
        #                 src_filter=src_filter,
        #             )

    @staticmethod
    def __match_pattern(
        src_nodes: Sequence[ASTNode],
        patterns: Sequence[ASTNode],
        depth: int,
        multiplicity: dict[str, int],
        pattern_match: Optional[PatternMatch],
        src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]],
    ) -> Optional[PatternMatch]:
        # if pattern_match is None:
        #     pattern_match = PatternMatch(src_nodes, patterns)
        #
        # indent = depth * 4  # for logging purposes only
        #
        # only_multi_wild_cards = all(p.kind == MATCH_ALL for p in patterns)
        # # if there are no patterns left or only multi wildcards left and no source nodes, return the current match
        # if len(patterns) == 0 or (only_multi_wild_cards and len(src_nodes) == 0):
        #     # only allow remaining srcNodes is this is the root level, depicted by depth == 0
        #     if len(src_nodes) > 0 and depth > 0:
        #         return None
        #     # we might end up with a multi wildcard at the end of the pattern list and no srcNodes left so add it
        #     if only_multi_wild_cards and len(patterns) == 1:
        #         pattern_match._query_create(patterns[0].get_name())
        #
        #     if MatchValidation.validate(pattern_match._key_matches):
        #         # srcNodes that are not (yet) matched are stored in the pattern match
        #         pattern_match._set_remaining_nodes(src_nodes)
        #         # remove the non-matching from the source nodes
        #         pattern_match.src_nodes = [
        #             n for n in pattern_match.src_nodes if n not in src_nodes
        #         ]
        #         return pattern_match
        #     return None
        #
        # # if patterns left but no source nodes, return None
        # if len(src_nodes) == 0:
        #     return None
        #
        # src_node = src_nodes[0]
        # pattern_node = patterns[0]
        #
        # if VERBOSE:
        #     do_log(
        #         indent,
        #         "\n** CHECKING **",
        #         src_node.get_text(),
        #         "** AGAINST **",
        #         pattern_node.get_text(),
        #         "\n",
        #     )
        #
        # if pattern_node.kind == MATCH_ALL:
        #     wildcard_match = pattern_match._query_create(pattern_node.get_name())
        #     greediness = multiplicity.get(pattern_node.get_name(), 0)
        #     if greediness <= len(wildcard_match.nodes) and len(patterns) > 1:
        #         # multiplicity of multi-wildcards is 0 so first try to match the next pattern with the current srcNodes
        #         # a clone is needed to keep the current state of the match when the next match fails
        #
        #         next_match = MatchFinder.__match_pattern(
        #             src_nodes,
        #             patterns[1:],
        #             depth,
        #             multiplicity,
        #             pattern_match.clone(),
        #             src_filter,
        #         )
        #         if next_match:
        #             return next_match
        #     wildcard_match._add_node(src_node)
        #
        #     if VERBOSE:
        #         do_log( indent,"** $$WILDCARD **",pattern_node.get_text(),"** MATCHES **", raw(wildcard_match.nodes),)
        #
        #     return MatchFinder.__match_pattern( src_nodes[1:], patterns, depth, multiplicity, pattern_match, src_filter)
        greedy = False
        foundPosition = 0
        foundPositionInExpandedList = 0
        # this case does not really make sense
        if len(patterns) ==1 and patterns[0].get_kind() ==MATCH_ALL:
            foundStatements.append(src_nodes)
            return
        if not patterns or len(patterns) ==0:
            return

        for i in range(len(src_nodes)):
            node = src_nodes[i]
            pattern = patterns[foundPosition]
            if pattern.kind == MATCH_ALL:
                greedy = True
                foundPosition += 1
                pattern = patterns[foundPosition]
                expansion_start = i
                # if foundPosition == 0:
                #     start = i
                # current_name = patterns[foundPosition].get_name()
                # if current_name in expansionList:
                #     if MatchUtils.is_match(expansionList[current_name][foundPositionInExpandedList], node):
                #         foundPositionInExpandedList = foundPositionInExpandedList + 1
                #         if (foundPositionInExpandedList == len(expansionList[current_name])):
                #             # found all match
                #             foundPositionInExpandedList = 0
                #             foundPosition += 1
                #     else:
                #         foundPosition = 0
                # else:
                #     foundPosition +=  1
                #     foundPositionInExpandedList = 0
                #     expansion_start = i
                #     i -= 1
                #     greedy = True
            if MatchUtils.is_match(node, pattern):
                if foundPosition == 0:
                    start = i
                if greedy == True:
                    greedy = False
                    last_name = patterns[foundPosition - 1].get_name()
                    if not last_name in expansionList:
                        expansionList[last_name] = src_nodes[expansion_start:i]
                        foundPositionInExpandedList = 0
                foundPosition = foundPosition + 1
                if foundPosition == len(patterns):
                    end = i + 1
                    # pattern_match._query_create(MatchUtils.EXACT_MATCH)

                    foundStatements.append(MatchResult(src_nodes[start:end], expansion, expansionList))
                    foundPosition = 0
            # elif node.expression and len(patterns)==1:
            #     MatchFinder.__match_pattern(
            #         [node.expression],
            #         patterns,
            #         depth,
            #         multiplicity,
            #         pattern_match,
            #         src_filter,
            #     )
            if node.get_children():
                MatchFinder.__match_pattern(
                    node.children,
                    patterns,
                    depth,
                    multiplicity,
                    pattern_match,
                    src_filter,
                )
            if node.orelse:
                MatchFinder.__match_pattern(
                    node.orelse,
                    patterns,
                    depth,
                    multiplicity,
                    pattern_match,
                    src_filter,
                )


        #
        # current=0
        # for i in range( len(src_nodes)):
        #     src_node = src_nodes[i]
        #     pattern_node = patterns[current]
        #     if MatchUtils.is_match( src_node, pattern_node):
        #         current += 1
        #         if pattern_node.kind == MATCH_ONE:
        #             wildcard_match = pattern_match._query_create(pattern_node.get_name())
        #             # TODO check with pierre whether we should take the highest or the deepest match
        #             # if not  wildcard_match.nodes:
        #             wildcard_match._add_node(src_node)
        #     else:
        #         # store the exact match because it might be needed to determine the location of a multi wildcard match without nodes
        #         pattern_match._query_create(MatchUtils.EXACT_MATCH)._add_node(src_node)
        #     if VERBOSE:
        #         do_log( indent, pattern_node.get_text(),"** MATCHES **",src_node.get_text())
        #
        #
        #     # invariant: a match is found if the current pattern and src node match and their successors match
        #     return MatchFinder.__match_pattern(
        #         src_nodes[1:],
        #         patterns[1:],
        #         depth,
        #         multiplicity,
        #         pattern_match,
        #         src_filter,
        #     )
        #
        # return None


class MatchValidation:
    @staticmethod
    def _check_duplicate_matches(key_matches: Sequence[KeyMatch]):
        """
        Checks for duplicate matches in the keyMatches attribute.

        This method groups the keyMatches by their keys and identifies groups with the same key.
        It then transposes the nodes in these groups to compare nodes at the same index across different groups.
        If any group of nodes at the same index do not match, the method returns False.

        Returns:
            bool: False if any group of nodes at the same index do not match, otherwise None.
        """
        key_groups: dict[str, list[list[ASTNode]]] = {}
        for key_match in [m for m in key_matches if MatchUtils.is_wildcard(m.key)]:
            if key_match.key not in key_groups:
                key_groups[key_match.key] = []
            # for single wildcards only the last/deepest node is relevant
            # an example of this is CallExpr where is matches twice once for the function and once for the function name
            # only the function name must be evaluated
            nodes = (
                key_match.nodes
                if MatchUtils.is_multi_wildcard(key_match.key)
                else key_match.nodes[-1:]
            )
            key_groups[key_match.key].append(nodes)
        for key, same in key_groups.items():
            if len(same) < 2:
                continue
            # cmp
            comp = same[0]
            for row in same[1:]:
                if len(comp) != len(row):
                    if VERBOSE:
                        do_log(
                            0,
                            "FAILED on duplicate matches having different lengths",
                            key,
                            f"first[{raw(comp)}]",
                            f" next[{raw(row)}]",
                        )
                    return False
                for col_idx, node in enumerate(row):
                    if not MatchFinder.is_match(comp[col_idx : col_idx + 1], [node]):
                        if VERBOSE:
                            do_log(
                                0,
                                "FAILED on duplicate matches not matching",
                                key,
                                " != ".join(
                                    ["[" + raw(comp) + "]", "[" + raw(row) + "]"]
                                ),
                            )
                        return False
        return True

    @staticmethod
    def _check_single_matches(key_matches: Sequence[KeyMatch]):
        """
        Checks for single matches in the keyMatches attribute.

        This method checks if any keyMatch has exactly  one node. If not the method returns False.

        Returns:
            bool: False if any keyMatch has more than one node, otherwise None.
        """
        result = all(
            len(key_match.nodes) > 0
            for key_match in key_matches
            if MatchUtils.is_single_wildcard(key_match.key)
        )
        if not result and VERBOSE:
            print(f"FAILED on single match")
        return result

    @staticmethod
    def validate(key_matches: Sequence[KeyMatch]):
        return MatchValidation._check_single_matches(
            key_matches
        ) and MatchValidation._check_duplicate_matches(key_matches)


def do_log(indent: int, *msgs: str):
    text = "\n".join(msgs)
    print(" ".join(f'{" "*indent}{l}' for l in text.splitlines()))


def raw(nodes: Sequence[ASTNode]):
    return " ".join([n.get_text() for n in nodes])

class MatchResult:
    def __init__(self, nodes, expansion, expansionList):
        self.nodes = nodes
        self.expansions = expansion
        self.expansionLists = expansionList