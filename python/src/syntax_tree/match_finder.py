from functools import cache
import re
from typing import Iterator, Optional

from common import Stream
from collections import Counter

from .ast_node import ASTNode

VERBOSE = False

class MatchUtils:

    EXACT_MATCH = 'EXACT_MATCH'

    @staticmethod
    def is_name_match(src: ASTNode, cmp: ASTNode)-> bool:
        return MatchUtils.is_wildcard(cmp) or src.get_name() == cmp.get_name()

    @staticmethod
    def is_match(src: ASTNode, cmp: ASTNode)-> bool:
        return MatchUtils.is_name_match(src,cmp) and  src.get_kind() == cmp.get_kind() and src.get_properties() == cmp.get_properties()

    @staticmethod
    def is_kind_match(src: ASTNode, cmp: ASTNode)-> bool:
        return src.get_kind() == cmp.get_kind()

    @staticmethod
    def is_wildcard(target: ASTNode|str)-> bool:
        return MatchUtils.is_single_wildcard(target) or MatchUtils.is_multi_wildcard(target)

    @staticmethod
    def is_multi_wildcard(target: ASTNode|str)-> bool:
        if isinstance(target, str):
            return target.startswith('$$')
        return MatchUtils.is_multi_wildcard(target.get_name())
    @staticmethod
    def is_single_wildcard(target: ASTNode|str)-> bool:
        if isinstance(target, str):
            return not MatchUtils.is_multi_wildcard(target) and target.startswith('$')
        return MatchUtils.is_single_wildcard(target.get_name())

    @staticmethod
    def exclude_nodes_by_kind(exclude_kind:str, nodes: list[ASTNode]):
        if exclude_kind:
            filtered_nodes = [node for node in nodes if re.search(exclude_kind,node.get_kind(), re.IGNORECASE)==None]
            return filtered_nodes
        return nodes


    @staticmethod
    def get_multi_wildcard_keys(patterns: list[ASTNode], result: list[str] = []) -> list[str]:
        """
        Recursively finds and returns the names of all multi-wildcard patterns in the given list of AST nodes.

        Args:
            patterns (list[ASTNode]): A list of ASTNode objects to search for multi-wildcard patterns.
            result (list, optional): A list to store the names of the multi-wildcard patterns found. Defaults to an empty list.

        Returns:
            list: A list containing the names of all multi-wildcard patterns found in the input list.
        """
        for pattern in patterns:
            if MatchUtils.is_multi_wildcard(pattern):
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
        for k,v in multiplicity.items():
            if v < 3:
                multiplicity[k] += 1
                return True
        return False

class KeyMatch:
    def clone(self) -> 'KeyMatch':
        cloned = KeyMatch(self.key)
        cloned.nodes = self.nodes[:]
        return cloned
    
    def __init__(self, key:str) -> None:
        self.key = key
        self.nodes: list[ASTNode] = []
        
    def _add_node(self, node: ASTNode):
        self.nodes.append(node)

class PatternMatch:
    def __init__(self, src_nodes: list[ASTNode], patterns: list[ASTNode]) -> None:
        self._key_matches: list[KeyMatch] = []
        self._remaining_nodes: list[ASTNode] = []
        self.src_nodes = src_nodes
        self.patterns = patterns

    def clone(self) -> 'PatternMatch':
        # create a new instance of the pattern match
        clone = PatternMatch(self.src_nodes, self.patterns)
        # clone the key matches
        clone._key_matches = [keyMatch.clone() for keyMatch in self._key_matches]
        clone._remaining_nodes = self._remaining_nodes[:]
        return clone

    def _query_create(self, key: str)-> KeyMatch:
        if self._key_matches and self._key_matches[-1].key==key:
            return self._key_matches[-1]
        self._key_matches.append(KeyMatch(key))
        return self._key_matches[-1]
   
    def _get_remaining_nodes(self)-> list[ASTNode]:
        return self._remaining_nodes

    def _set_remaining_nodes(self, nodes: list[ASTNode]):
        self._remaining_nodes = nodes
    
    @cache
    def get_nodes(self) -> dict[str, list[ASTNode]]:
        # take the deepest found match for each wildcard key
        return {key_match.key: [key_match.nodes[-1]] if MatchUtils.is_single_wildcard(key_match.key) else key_match.nodes for key_match in self._key_matches if MatchUtils.is_wildcard(key_match.key) }

    @cache
    def get_raw_signatures(self) -> dict[str, str]:
        nodes = self.get_nodes()
        def get_raw_signature(key:str, location: tuple[int,int]) -> str:
            matched_nodes = nodes.get(key, [])
            if(not matched_nodes or location[1]==0):
                return ''
            return matched_nodes[0].root.get_binary_file_content()[matched_nodes[0].get_start_offset():matched_nodes[-1].get_end_offset()].decode('utf-8')
        return {k:get_raw_signature(k,v) for k,v in self.get_locations().items()}

    @cache
    def get_names(self) -> dict[str, str]:
        return {k:v[0].get_name() for k,v in self.get_nodes().items()}

    @cache
    def get_locations(self) -> dict[str, tuple[int,int]]:
        result = {}
        location = 0
        length = 0
        for key_match in self._key_matches:
            # take the first node of the key match or the last location + length if the preceding match does not have a node
            location = key_match.nodes[-1].get_start_offset() if key_match.nodes else location + length 
            length = key_match.nodes[-1].get_length() if key_match.nodes else 0
            if MatchUtils.is_wildcard(key_match.key):
                result[key_match.key] = (location, length)
        return result
    
    def compose_replacement(self, replacement:str)-> str:
        for placeholder, raw_signature in self.get_raw_signatures().items():
            quoted_placeholder = re.escape(placeholder)
            while placeholder in replacement:
                pattern = re.compile(r"( *)" + quoted_placeholder)
                matcher = pattern.search(replacement)

                if matcher:
                    spaces = matcher[1]
                    indent_replacement = raw_signature.replace("\n", "\n" + spaces)
                    index = replacement.index(placeholder)
                    # replace the placeholder with the indent replacement
                    replacement = replacement[:index] + indent_replacement + replacement[index + len(placeholder):]
                else:
                    print("Match doesn't match unexpectedly")
        return replacement
        

class MatchFinder:

    DEFAULT_EXCLUDE_KIND = 'comment'

    @staticmethod
    def find_all(src_nodes: list[ASTNode]|ASTNode, *patterns_list: list[ASTNode], recursive=True, exclude_kind=DEFAULT_EXCLUDE_KIND)-> Stream[PatternMatch]:
        """
        Finds all pattern matches in the given source nodes.

        Args:
            src_nodes (list[ASTNode] | ASTNode): The source nodes to search within. Can be a single ASTNode or a list of ASTNodes.
            *patterns_list (list[ASTNode]): One or more lists of ASTNodes representing the patterns to match.
            recursive (bool, optional): Whether to search recursively within the source nodes. Defaults to True.
            exclude_kind (type, optional): The kind of nodes to exclude from the search. Defaults to DEFAULT_EXCLUDE_KIND.

        Returns:
            Stream[PatternMatch]: A stream of pattern matches found in the source nodes.
        """
        if not isinstance(src_nodes, list): 
            src_nodes = [src_nodes]
        return Stream(MatchFinder.__find_all(src_nodes, *patterns_list, recursive=recursive, exclude_kind=exclude_kind))

    @staticmethod
    def match_pattern(src_nodes: list[ASTNode]|ASTNode, patterns: list[ASTNode], exclude_kind=DEFAULT_EXCLUDE_KIND)-> Optional[PatternMatch]:
        """
        Matches a given source node or list of source nodes against a list of pattern nodes.

        Args:
            src_nodes (list[ASTNode] | ASTNode): The source node or list of source nodes to be matched.
            patterns (list[ASTNode]): The list of pattern nodes to match against the source nodes.
            exclude_kind: The kind of nodes to exclude from matching, defaults to DEFAULT_EXCLUDE_KIND.

        Returns:
            Optional[PatternMatch]: A PatternMatch object if a match is found, otherwise None.
        """
        if isinstance(src_nodes, ASTNode):
            src_nodes = [src_nodes]
        patterns = MatchUtils.exclude_nodes_by_kind(exclude_kind,patterns) # exclude nodes by kind
        keys = MatchUtils.get_multi_wildcard_keys(patterns)
        multiplicity  = {key:0 for key,count in Counter(keys).items() if count > 1}
                # remove the last item from multiplicity because it the last item is already greedy
        if len(multiplicity) > 1:
            multiplicity.popitem()
        has_next_multiplicity = True
        while  has_next_multiplicity:
            pattern_match = MatchFinder.__match_pattern(src_nodes, patterns, 0, multiplicity, None, exclude_kind=exclude_kind)
            if pattern_match:
                return  pattern_match
            has_next_multiplicity = MatchUtils.next_multiplicity(multiplicity)
        return None

    @staticmethod
    def is_match(src1: ASTNode|list[ASTNode], src2: ASTNode|list[ASTNode], exclude_kind=DEFAULT_EXCLUDE_KIND) -> bool:
        if isinstance(src2, ASTNode):
            src2 = [src2]
        return MatchFinder.match_pattern(src1, src2, exclude_kind=exclude_kind) is not None

    @staticmethod
    def __find_all(src_nodes: list[ASTNode], *patterns_list: list[ASTNode], recursive:bool, exclude_kind:str)-> Iterator[PatternMatch]:
        target_nodes = MatchUtils.exclude_nodes_by_kind(exclude_kind,src_nodes) # exclude nodes by kind

        while target_nodes:
            pattern_match = None
            for patterns in patterns_list:
                pattern_match = MatchFinder.match_pattern(target_nodes, patterns, exclude_kind)
                if pattern_match:
                    break # only one match is needed

            if pattern_match:
                target_nodes = pattern_match._get_remaining_nodes()
                if VERBOSE: do_log("VALID MATCH FOUND")
                yield pattern_match
            else:
                target_nodes = target_nodes[1:] # skip the first node
        #recursively evaluate all children
        if recursive:
            for node in src_nodes:
                yield from MatchFinder.__find_all(node.get_children(), *patterns_list, recursive=recursive, exclude_kind=exclude_kind)

    @staticmethod
    def __match_pattern(src_nodes: list[ASTNode], patterns: list[ASTNode],  depth, multiplicity: dict[str,int], patternMatch: Optional[PatternMatch], exclude_kind:str)-> Optional[PatternMatch]:
        if patternMatch is None:
            patternMatch = PatternMatch(src_nodes, patterns)

        indent = depth*4 # for logging purposes only

        only_multi_wild_cards = all(MatchUtils.is_multi_wildcard(p) for p in patterns)
        # if there are no patterns left or only multi wildcards left and no source nodes, return the current match
        if len(patterns) == 0 or (only_multi_wild_cards and len(src_nodes) == 0):
            #only allow remaining srcNodes is this is the root level, depicted by depth == 0
            if len(src_nodes) > 0 and depth >0:
                return None
            # we might end up with a multi wildcard at the end of the pattern list and no srcNodes left so add it
            if only_multi_wild_cards and len(patterns) == 1:
                patternMatch._query_create(patterns[0].get_name())

            if MatchValidation.validate(patternMatch._key_matches):
                # srcNodes that are not (yet) matched are stored in the pattern match
                patternMatch._set_remaining_nodes(src_nodes)
                #remove the non matching from the source nodes
                patternMatch.src_nodes = [n for n in patternMatch.src_nodes if n not in src_nodes]
                return patternMatch
            return None

        # if patterns left but no source nodes, return None
        if(len(src_nodes) == 0):
            return None

        src_node = src_nodes[0]
        pattern_node = patterns[0]

        if VERBOSE: do_log(indent, '\n** CHECKING **',src_node.get_raw_signature(),'** AGAINST **',pattern_node.get_raw_signature(), '\n')

        if MatchUtils.is_multi_wildcard(pattern_node):
            wildcard_match = patternMatch._query_create(pattern_node.get_name())
            greediness = multiplicity.get(pattern_node.get_name(),0)
            if greediness <= len(wildcard_match.nodes) and len(patterns) > 1:
                # multiplicity of multi-wildcards is 0 so first try to match the next pattern with the current srcNodes
                # a clone is needed to keep the current state of the match when the next match fails

                nextMatch = MatchFinder.__match_pattern(src_nodes, patterns[1:], depth, multiplicity, patternMatch.clone(), exclude_kind)
                if nextMatch:                 
                    return nextMatch  
            wildcard_match._add_node(src_node)

            if VERBOSE: do_log(indent, "** $$WILDCARD **",pattern_node.get_raw_signature(),"** MATCHES **",raw(wildcard_match.nodes))
            return MatchFinder.__match_pattern(src_nodes[1:], patterns, depth, multiplicity, patternMatch, exclude_kind)
        elif MatchUtils.is_single_wildcard(pattern_node) or MatchUtils.is_match(src_node, pattern_node):
            if pattern_node.is_statement() and not src_node.is_statement(): # type: ignore
                return None
            # if the pattern node has children then kind must match (to distinct for instance while and if)
            if pattern_node.get_children() and (not MatchUtils.is_kind_match(src_node, pattern_node)):
                return None
            
            if MatchUtils.is_single_wildcard(pattern_node):
                wildcard_match = patternMatch._query_create(pattern_node.get_name())
                # TODO check with pierre whether we should take the highest or the deepest match
                if not  wildcard_match.nodes: 
                    wildcard_match._add_node(src_node)
            else:
                # store the exact match because it might be needed to determine the location of a multi wildcard match without nodes
                patternMatch._query_create(MatchUtils.EXACT_MATCH)._add_node(src_node)
            if VERBOSE: do_log(indent,pattern_node.get_raw_signature(),'** MATCHES **',src_node.get_raw_signature())

            # the current match is found if the current pattern and src node match and their children match
            if pattern_node.get_children():
                src_child_nodes = MatchUtils.exclude_nodes_by_kind(exclude_kind,src_node.get_children())
                pattern_child_nodes = MatchUtils.exclude_nodes_by_kind(exclude_kind,pattern_node.get_children())
                foundMatch =  MatchFinder.__match_pattern(src_child_nodes, pattern_child_nodes, depth+1, multiplicity,patternMatch,exclude_kind)
                if not foundMatch:
                    return None
                patternMatch = foundMatch # update the pattern match with the result of the child
            # invariant: a match is found if the current pattern and src node match and their successors match
            return MatchFinder.__match_pattern(src_nodes[1:], patterns[1:], depth, multiplicity, patternMatch, exclude_kind)
        return None


class MatchValidation:
    @staticmethod
    def _check_duplicate_matches(key_matches: list[KeyMatch]):
        """
        Checks for duplicate matches in the keyMatches attribute.

        This method groups the keyMatches by their keys and identifies groups with the same key.
        It then transposes the nodes in these groups to compare nodes at the same index across different groups.
        If any group of nodes at the same index do not match, the method returns False.

        Returns:
            bool: False if any group of nodes at the same index do not match, otherwise None.
        """
        key_groups = {}
        for key_match in [m for m in key_matches if MatchUtils.is_wildcard(m.key)]:
            if key_match.key not in key_groups:
                key_groups[key_match.key] = []
            key_groups[key_match.key].append(key_match.nodes)
        for key, same in key_groups.items():
            if len(same) < 2:
                continue
            # cmp
            comp = same[0]
            for row in same[1:]:
                if len(comp) != len(row):
                    if VERBOSE: do_log(0,f"FAILED on duplicate matches having different lengths", key, f'first[{raw(comp)}]', f' next[{raw(row)}]')
                    return False
                for col_idx, node in enumerate(row):
                    if not MatchFinder.is_match(comp[col_idx:col_idx+1], [node]):
                        if VERBOSE: do_log(0,f"FAILED on duplicate matches not matching", key, ' != '.join(['['+raw(comp)+']' ,'['+raw(row)+']']))    
                        return False
        return True
    @staticmethod
    def _check_single_matches(key_matches: list[KeyMatch]):
        """
        Checks for single matches in the keyMatches attribute.

        This method checks if any keyMatch has exactly  one node. If not the method returns False.

        Returns:
            bool: False if any keyMatch has more than one node, otherwise None.
        """
        result =  all(len(key_match.nodes) > 0 for key_match in key_matches if MatchUtils.is_single_wildcard(key_match.key))
        if not result and VERBOSE:
            print(f"FAILED on single match")
        return result

    @staticmethod
    def validate(key_matches: list[KeyMatch]):
        return MatchValidation._check_single_matches(key_matches) and MatchValidation._check_duplicate_matches(key_matches)

def do_log(indent, *msgs: str):
    text = '\n'.join(msgs)
    print('\n'.join(f'{" "*indent}{l}' for l in text.splitlines()))

def raw(nodes: list[ASTNode]):
    return ' '.join([n.get_raw_signature() for n in nodes])

