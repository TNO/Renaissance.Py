from typing import Iterator, Optional
from .ast_node import ASTNode
from collections import Counter

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
    def add_node(self, node: ASTNode):
        self.nodes.append(node)

class PatternMatch:
    def __init__(self, src_nodes: list[ASTNode], patterns: list[ASTNode]) -> None:
        self.keyMatches: list[KeyMatch] = []
        self.remaining_nodes: list[ASTNode] = []
        self.src_nodes = src_nodes
        self.patterns = patterns

    def clone(self) -> 'PatternMatch':
        # create a new instance of the pattern match
        clone = PatternMatch(self.src_nodes, self.patterns)
        # clone the key matches
        clone.keyMatches = [keyMatch.clone() for keyMatch in self.keyMatches]
        clone.remaining_nodes = self.remaining_nodes[:]
        return clone

    def query_create(self, key: str)-> KeyMatch:
        if self.keyMatches and self.keyMatches[-1].key==key:
            return self.keyMatches[-1]
        self.keyMatches.append(KeyMatch(key))
        return self.keyMatches[-1]
   
    def get_remaining_nodes(self)-> list[ASTNode]:
        return self.remaining_nodes

    def set_remaining_nodes(self, nodes: list[ASTNode]):
        self.remaining_nodes = nodes
    
    def get_dict(self):
        # TODO check with Pierre whether we should take the highest or the deepest match for single wildcards
        #currently we choose the first match
        return {keyMatch.key: [keyMatch.nodes[-1]] if MatchUtils.is_single_wildcard(keyMatch.key) else keyMatch.nodes for keyMatch in self.keyMatches if MatchUtils.is_wildcard(keyMatch.key) }

    def get_locations(self):
        result = {}
        location = 0
        length = 0
        for keyMatch in self.keyMatches:
            # take the first node of the key match or the last location + length if the preceding match does not have a node
            location = keyMatch.nodes[0].get_start_offset() if keyMatch.nodes else location + length 
            length = keyMatch.nodes[0].get_length() if keyMatch.nodes else 0
            if MatchUtils.is_wildcard(keyMatch.key):
                result[keyMatch.key] = (location, length)
        return result

    def validate(self):
        return MatchValidation._check_single_matches(self.keyMatches) and MatchValidation._check_duplicate_matches(self.keyMatches)

class MatchFinder:

    @staticmethod
    def find_all(srcNodes: list[ASTNode], *patterns_list: list[ASTNode], recursive=True)-> Iterator[PatternMatch]:
        """
        Finds all matches of the given patterns in the source nodes.
        Args:
            srcNodes (list[ASTNode]): The list of source nodes to search within.
            *patterns_list (list[ASTNode]): Variable length argument list of patterns to match against the source nodes.
            recursive (bool): Whether to search recursively through all children of the source nodes.
        Yields:
            Iterator[PatternMatch]: An iterator of PatternMatch objects representing the matches found.
        Note:
            - The search will yield only the first pattern matched found for source node.
            - The search will continue recursively through all children of the source nodes if recursive is true.
            - Nodes found in a match will not be included in subsequent matches.
        """
        targetNodes = srcNodes


        while targetNodes:
            for patterns in patterns_list:
                keys = MatchUtils.get_multi_wildcard_keys(patterns)
                multiplicity  = {key:0 for key,count in Counter(keys).items() if count > 1}
                # remove the last item from multiplicity because it the last item is already greedy
                if len(multiplicity) > 1:
                    multiplicity.popitem()
                while True:
                    pattern_match = MatchFinder.match_pattern(targetNodes, patterns, 0, multiplicity)
                    if pattern_match or not MatchUtils.next_multiplicity(multiplicity):
                        break

                if pattern_match:
                    targetNodes = pattern_match.get_remaining_nodes()
                    if VERBOSE: do_log("VALID MATCH FOUND")

                    yield pattern_match
                    break # only one match is needed
                else:
                    targetNodes = targetNodes[1:] # skip the first node
        #recursively evaluate all children
        if recursive:
            for node in srcNodes:
                yield from MatchFinder.find_all(node.get_children(), *patterns_list)

    @staticmethod
    def match_pattern(srcNodes: list[ASTNode], patterns: list[ASTNode],  depth, multiplicity: dict[str,int], patternMatch: Optional[PatternMatch]=None,)-> Optional[PatternMatch]:
        """
        Matches a given pattern against the provided source nodes.
        Args:
            patternMatch (PatternMatch): The current pattern match state.
            srcNodes (list[ASTNode]): The list of source nodes to match against.
            patterns (list[ASTNode]): The list of pattern nodes to match.
            depth (int): The depth of the current match in the pattern tree.
        Returns:
            Optional[PatternMatch]: The updated pattern match if the pattern is successfully matched and validated,
                                    otherwise None.
        """
        if patternMatch is None:
            patternMatch = PatternMatch(srcNodes, patterns)

        indent = depth*4 # for logging purposes only

        only_multi_wild_cards = all(MatchUtils.is_multi_wildcard(p) for p in patterns)
        # if there are no patterns left or only multi wildcards left and no source nodes, return the current match
        if len(patterns) == 0 or (only_multi_wild_cards and len(srcNodes) == 0):
            #only allow remaining srcNodes is this is the root level, depicted by depth == 0
            if len(srcNodes) > 0 and depth >0:
                return None
            # we might end up with a multi wildcard at the end of the pattern list and no srcNodes left so add it
            if only_multi_wild_cards and len(patterns) == 1:
                patternMatch.query_create(patterns[0].get_name())

            if patternMatch.validate():
                patternMatch.set_remaining_nodes(srcNodes)
                return patternMatch
            return None

        # if patterns left but no source nodes, return None
        if(len(srcNodes) == 0):
            return None

        srcNode = srcNodes[0]
        patternNode = patterns[0]

        if VERBOSE: do_log(indent, '\n** CHECKING **',srcNode.get_raw_signature(),'** AGAINST **',patternNode.get_raw_signature(), '\n')

        if MatchUtils.is_multi_wildcard(patternNode):
            wildcard_match = patternMatch.query_create(patternNode.get_name())
            greediness = multiplicity.get(patternNode.get_name(),0)
            if greediness <= len(wildcard_match.nodes) and len(patterns) > 1:
                # multiplicity of multi-wildcards is 0 so first try to match the next pattern with the current srcNodes
                # a clone is needed to keep the current state of the match when the next match fails

                nextMatch = MatchFinder.match_pattern(srcNodes, patterns[1:], depth, multiplicity, patternMatch.clone())
                if nextMatch:                 
                    return nextMatch  
            wildcard_match.add_node(srcNode)

            if VERBOSE: do_log(indent, "** $$WILDCARD **",patternNode.get_raw_signature(),"** MATCHES **",raw(wildcard_match.nodes))
            return MatchFinder.match_pattern(srcNodes[1:], patterns, depth, multiplicity, patternMatch)
        elif MatchUtils.is_single_wildcard(patternNode) or MatchUtils.is_match(srcNode, patternNode):
            if patternNode.is_statement() and not srcNode.is_statement(): # type: ignore
                return None
            # if the pattern node has children then kind must match (to distinct for instance while and if)
            if patternNode.get_children() and (not MatchUtils.is_kind_match(srcNode, patternNode)):
                return None
            
            if MatchUtils.is_single_wildcard(patternNode):
                wildcard_match = patternMatch.query_create(patternNode.get_name())
                # TODO check with pierre whether we should take the highest or the deepest match
                if not  wildcard_match.nodes: 
                    wildcard_match.add_node(srcNode)
            else:
                # store the exact match because it might be needed to determine the location of a multi wildcard match without nodes
                patternMatch.query_create(MatchUtils.EXACT_MATCH).add_node(srcNode)
            if VERBOSE: do_log(indent,patternNode.get_raw_signature(),'** MATCHES **',srcNode.get_raw_signature())

            # the current match is found if the current pattern and src node match and their children match
            if patternNode.get_children():
                foundMatch =  MatchFinder.match_pattern(srcNode.get_children(), patternNode.get_children(), depth+1, multiplicity,patternMatch)
                if not foundMatch:
                    return None
                patternMatch = foundMatch # update the pattern match with the result of the child
            # invariant: a match is found if the current pattern and src node match and their successors match
            return MatchFinder.match_pattern(srcNodes[1:], patterns[1:], depth, multiplicity, patternMatch)
        return None

class MatchValidation:
    @staticmethod
    def _check_duplicate_matches(keyMatches: list[KeyMatch]):
        """
        Checks for duplicate matches in the keyMatches attribute.

        This method groups the keyMatches by their keys and identifies groups with the same key.
        It then transposes the nodes in these groups to compare nodes at the same index across different groups.
        If any group of nodes at the same index do not match, the method returns False.

        Returns:
            bool: False if any group of nodes at the same index do not match, otherwise None.
        """
        keyGroups = {}
        for keyMatch in [m for m in keyMatches if MatchUtils.is_wildcard(m.key)]:
            if keyMatch.key not in keyGroups:
                keyGroups[keyMatch.key] = []
            keyGroups[keyMatch.key].append(keyMatch.nodes)
        for key, same in keyGroups.items():
            if len(same) < 2:
                continue
            # cmp
            comp = same[0]
            for row in same[1:]:
                if len(comp) != len(row):
                    if VERBOSE: do_log(0,f"FAILED on duplicate matches having different lengths", key, f'first[{raw(comp)}]', f' next[{raw(row)}]')
                    return False
                for colIdx, node in enumerate(row):
                    if not MatchFinder.match_pattern(comp[colIdx:colIdx+1], [node],0,{}):
                        if VERBOSE: do_log(0,f"FAILED on duplicate matches not matching", key, ' != '.join(['['+raw(comp)+']' ,'['+raw(row)+']']))    
                        return False
        return True
    @staticmethod
    def _check_single_matches(keyMatches: list[KeyMatch]):
        """
        Checks for single matches in the keyMatches attribute.

        This method checks if any keyMatch has exactly  one node. If not the method returns False.

        Returns:
            bool: False if any keyMatch has more than one node, otherwise None.
        """
        result =  all(len(keyMatch.nodes) > 0 for keyMatch in keyMatches if MatchUtils.is_single_wildcard(keyMatch.key))
        if not result and VERBOSE:
            print(f"FAILED on single match")
        return result

def do_log(indent, *msgs: str):
    text = '\n'.join(msgs)
    print('\n'.join(f'{" "*indent}{l}' for l in text.splitlines()))

def raw(nodes: list[ASTNode]):
    return ' '.join([n.get_raw_signature() for n in nodes])

