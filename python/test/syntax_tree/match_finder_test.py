from __future__ import annotations

import unittest
from unittest import TestCase

from unittest.mock import Mock

from impl.clang import ClangASTNode
from syntax_tree import ASTNode, ASTFactory, CPatternFactory, ASTFinder, ASTShower
from syntax_tree.match_finder import is_match, MatchFinder

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"
class SmallNodeTest(unittest.TestCase):
    pass
    # @parameterized.expand(Factories.extend([
    #     ('void f() {const char* bar = BAR;}', '(?i)Decl_?Stmt', ['const char* bar = BAR;'], {}),
    #     ('void f() {const char* foo = FOO;}', '(?i)Decl_?Stmt', ['const char* foo = FOO;'], {}),
    #     ('void f() {const char* same = SAME;}', '(?i)Decl_?Stmt', ['const char* same = SAME;'], {}),
    #     ('void f() {const char* $name = BAR;}', '(?i)Decl_?Stmt', ['const char* bar = BAR;'], {'$name': ['bar']}),
    #     ('void f() {const char* $name = FOO;}', '(?i)Decl_?Stmt', ['const char* foo = FOO;'], {'$name': ['foo']}),
    #     ('void f() {const char* $name = SAME;}', '(?i)Decl_?Stmt', ['const char* same = SAME;'],
    #      {'$name': ['same']}),
    #     ('const char* $$args; void f() { printf($$args);}', '(?i)Call_?Expr',
    #      ['printf("%s %s %s", foo, bar, same);'], {'$$args': ['"%s %s %s"', 'foo', 'bar', 'same']}),
    # ]))
    # def test_small_pieces(self):
    #     code = """
    #     #define BAR "bar"
    #     const char* bar = BAR;
    #     int f(){
    #         const char* bar = BAR;
    #     }
    #     """
    #     factory = ASTFactory(ClangASTNode, [])
    #     atu = factory.create_from_text(code, 'test.c')
    #     patternFactory = CPatternFactory(factory, ref_node=atu)
    #     statementsAtu = patternFactory.create('void f() {const char* bar = BAR;}')
    #     statements = ASTFinder.find_kind(statementsAtu, '(?i)Decl_?Stmt').find_last().get()  # pick the last statement
    #     ASTShower.show_node(atu, include_properties=True)
    #
    #     result = MatchFinder.find_all(atu, [statements], recursive=True).to_list()
    #     result[0].nodes[0]
    #         # .map(lambda match: match.nodes[0])
    #         # .filter(ASTNode.is_part_of_translation_unit)
    #         # .map(ASTNode.text).to_list())
    #     self.assertEqual('expected', result)
# class MatchUtilsTest(TestCase):
#
#
#     def test_is_match(self):
#         src = Mock(scpe=ASTNode)
#         comp = Mock(scpe=ASTNode)
#         src.get_name.return_value ="name"
#         src.get_kind.return_value ="kind"
#         src.get_properties.return_value = []
#         comp.get_name.return_value = "name"
#         comp.get_kind.return_value = "kind"
#         comp.get_properties.return_value = []
#         self.assertTrue(is_match(src, comp))
#         comp.get_properties.return_value = ['props']
#         self.assertFalse(is_match(src, comp))
#         comp.get_properties.return_value = []
#         comp.get_kind.return_value = 'other'
#         self.assertFalse(is_match(src, comp))
#         comp.get_kind.return_value = 'kind'
#         comp.get_name.return_value = 'my_awesome_name'
#         self.assertFalse(is_match(src, comp))
#         comp.get_name.return_value = '$my_awesome_name'
#         self.assertTrue(is_match(src, comp))

    # def test_is_name_match(self):
    #     mock = Mock(scpe = ASTNode)
    #     res = MatchUtils.is_name_match(mock, "$name")
    #     self.assertTrue(res)
    # def test_is_wildcard(self):
    #     self.assertTrue(MatchUtils.is_wildcard("$$stmts"))
    #     self.assertTrue(MatchUtils.is_wildcard("$stmt"))
    #     self.assertTrue(MatchUtils.is_wildcard("$"))
    #     self.assertTrue(MatchUtils.is_wildcard("$$"))
    #     # should work?
    #     node = Mock(scpe=ASTNode)
    #     node.get_name.return_value = "$my_awesome_name"
    #     self.assertTrue(MatchUtils.is_wildcard(node))
    #
    #
    #
    # def test_is_multi_wildcard(self):
    #     self.assertTrue(MatchUtils.is_multi_wildcard("$$stmts"))
    #     self.assertFalse(MatchUtils.is_multi_wildcard("$stmt"))
    #     self.assertFalse(MatchUtils.is_multi_wildcard("$"))
    #     self.assertTrue(MatchUtils.is_multi_wildcard("$$"))
    #     # should work?
    #     node = Mock(scpe=ASTNode)
    #     node.get_name.return_value = "$$my_awesome_name"
    #     self.assertTrue(MatchUtils.is_multi_wildcard(node))
    #
    # def test_is_single_wildcard(self):
    #     self.assertFalse(MatchUtils.is_single_wildcard("$$stmts"))
    #     self.assertTrue(MatchUtils.is_single_wildcard("$stmt"))
    #     self.assertTrue(MatchUtils.is_single_wildcard("$"))
    #     self.assertFalse(MatchUtils.is_single_wildcard(None))
    #     # should work?
    #     node = Mock(scpe=ASTNode)
    #     node.get_name.return_value = "$my_awesome_name"
    #     self.assertTrue(MatchUtils.is_single_wildcard(node))
    # def test_exclude_nodes_by_kind(self):
    #     node = Mock(scpe=ASTNode)
    #     node.get_kind.return_value = "If"
    #     filtered =MatchUtils.exclude_nodes_by_kind('If', [node])
    #     self.assertNotIn(node , filtered)
    #     self.assertIn(node , MatchUtils.exclude_nodes_by_kind('While', [node]))
    #
    # def test_get_multi_wildcard_keys(
    #     patterns: Sequence[ASTNode], result: list[str] = []
    #         # TODO: replace mutable default argument
    # ) -> list[str]:
    #     for pattern in patterns:
    #         if MatchUtils.is_multi_wildcard(pattern):
    #             result.append(pattern.name)
    #         MatchUtils.get_multi_wildcard_keys(pattern.children, result)
    #     return result

#     def next_multiplicity(multiplicity: dict[str, int]):
#         """
#         Increments the value of the first key in the dictionary `multiplicity` that has a value less than 3.
#
#         Args:
#             multiplicity (dict[str, int]): A dictionary where keys are strings and values are integers.
#
#         Returns:
#             bool: True if a value was incremented, False if all values are 3 or greater.
#         """
#         for k, v in multiplicity.items():
#             if v < 3:
#                 multiplicity[k] += 1
#                 return True
#         return False
#
#
# class KeyMatch:
#     def clone(self) -> KeyMatch:
#         cloned = KeyMatch(self.key)
#         cloned.nodes = self.nodes[:]
#         return cloned
#
#     def __init__(self, key: str) -> None:
#         self.key = key
#         self.nodes: list[ASTNode] = []
#
#     def _add_node(self, node: ASTNode):
#         self.nodes.append(node)
#
#
# class PatternMatch:
#     def __init__(
#         self, src_nodes: Sequence[ASTNode], patterns: Sequence[ASTNode]
#     ) -> None:
#         self._key_matches: list[KeyMatch] = []
#         self._remaining_nodes: list[ASTNode] = []
#         self.src_nodes: Sequence[ASTNode] = src_nodes
#         self.patterns = patterns
#
#     def clone(self) -> PatternMatch:
#         # create a new instance of the pattern match
#         clone = PatternMatch(self.src_nodes, self.patterns)
#         # clone the key matches
#         clone._key_matches = [keyMatch.clone() for keyMatch in self._key_matches]
#         clone._remaining_nodes = self._remaining_nodes[:]
#         return clone
#
#     def _query_create(self, key: str) -> KeyMatch:
#         if self._key_matches and self._key_matches[-1].key == key:
#             return self._key_matches[-1]
#         self._key_matches.append(KeyMatch(key))
#         return self._key_matches[-1]
#
#     def _get_remaining_nodes(self) -> Sequence[ASTNode]:
#         return self._remaining_nodes
#
#     def _set_remaining_nodes(self, nodes: Sequence[ASTNode]):
#         self._remaining_nodes = list(nodes)
#
#     @cache
#     def get_nodes(self) -> dict[str, Sequence[ASTNode]]:
#         # take the deepest found match for each wildcard key
#         return {
#             key_match.key: (
#                 [key_match.nodes[-1]]       #TODO: What other nodes are in the key_match? Why is this needed?
#                 if MatchUtils.is_single_wildcard(key_match.key)
#                 else key_match.nodes
#             )
#             for key_match in self._key_matches
#             if MatchUtils.is_wildcard(key_match.key)
#         }
#
#     @cache
#     def get_raw_signatures(self) -> dict[str, str]:
#         nodes = self.get_nodes()
#
#         def get_raw_signature(key: str, location: tuple[int, int]) -> str:
#             matched_nodes = nodes.get(key, [])
#             if not matched_nodes or location[1] == 0:
#                 return ""
#             return (
#                 matched_nodes[0]
#                 .root.get_binary_file_content()[
#                     matched_nodes[0]
#                     .get_start_offset() : matched_nodes[-1]
#                     .get_end_offset()
#                 ]
#                 .decode(sys.getfilesystemencoding())
#             )
#
#         return {k: get_raw_signature(k, v) for k, v in self.get_locations().items()}
#
#     @cache
#     def get_names(self) -> dict[str, list[str]]:
#         return {k: [vi.get_name() for vi in v] for k, v in self.get_nodes().items()}
#
#     @cache
#     def get_locations(self) -> dict[str, tuple[int, int]]:
#         result: dict[str, tuple[int, int]] = {}
#         location = 0
#         length = 0
#         for key_match in self._key_matches:
#             # take the first node of the key match or the last location + length if the preceding match does not have a node
#             location = (
#                 key_match.nodes[-1].get_start_offset()
#                 if key_match.nodes
#                 else location + length
#             )
#             length = key_match.nodes[-1].get_length() if key_match.nodes else 0
#             if MatchUtils.is_wildcard(key_match.key):
#                 result[key_match.key] = (location, length)
#         return result
#
#     # utilities methods
#     def get_name(self, key: str) -> str:
#         result = self.get_names().get(key, [])
#         assert len(result) == 1, f"Only one name is expected for key {key}"
#         return result[0]
#
#     def get_text(self, key: str) -> str:
#         result = self.get_nodes().get(key, [])
#         assert len(result) == 1, f"Only one node is expected for key {key}"
#         return result[0].get_text()
#
#     def get_as_int(self, key: str) -> int:
#         return int(self.get_text(key))
#
#     def get_as_float(self, key: str) -> float:
#         return float(self.get_text(key))
#
#     def get_references(self) -> Sequence[ASTReference]:
#         return [ref for n in self.src_nodes for ref in n.get_references()]
#
#     def get_referenced_by(self) -> Sequence[ASTReference]:
#         return [ref for n in self.src_nodes for ref in n.get_referenced_by()]
#
#     def match_referenced_by(
#         self,
#         *patterns_list: Sequence[ASTNode]|ConstrainedPattern,
#         recursive: bool = True,
#         exclude_kind: str = DEFAULT_EXCLUDE_KIND,
#         part_of_translation_unit: bool = True,
#     ) -> Stream[PatternMatch]:
#         return Stream(
#             self._match_referenced_by(
#                 patterns_list, recursive, exclude_kind, part_of_translation_unit
#             )
#         )
#
#     def match_references(
#         self,
#         *patterns_list: Sequence[ASTNode]|ConstrainedPattern,
#         recursive: bool = True,
#         exclude_kind: str = DEFAULT_EXCLUDE_KIND,
#         part_of_translation_unit: bool = True,
#     ) -> Stream[PatternMatch]:
#         return Stream(
#             self._match_references(
#                 patterns_list, recursive, exclude_kind, part_of_translation_unit
#             )
#         )
#
#     def _match_referenced_by(
#         self,
#         patterns_list: Sequence[Sequence[ASTNode]|ConstrainedPattern],
#         recursive: bool,
#         exclude_kind: str,
#         part_of_translation_unit: bool,
#     ) -> Iterable[PatternMatch]:
#         for n in self.src_nodes:
#             for ref in n.get_referenced_by():
#                 yield from MatchFinder.find_all_strict(
#                     ref.get_node(),
#                     patterns_list,
#                     recursive,
#                     exclude_kind,
#                     part_of_translation_unit,
#                 ).to_iterable()
#
#     def _match_references(
#         self, patterns_list : Sequence[Sequence[ASTNode]|ConstrainedPattern],
#         recursive: bool, exclude_kind: str, part_of_translation_unit: bool
#     ) -> Iterable[PatternMatch]:
#         for n in self.src_nodes:
#             for ref in n.get_references():
#                 yield from MatchFinder.find_all_strict(
#                     [ref.get_node()],
#                     patterns_list,
#                     recursive,
#                     exclude_kind,
#                     part_of_translation_unit,
#                 ).to_iterable()
#
#     @staticmethod
#     def is_multi(placeholder: str):
#         return MatchUtils.is_multi_wildcard(placeholder)
#
#
# #TODO: do we want to merge the filter functionality with the find pattern?
# @dataclass(frozen=True)
# class ConstrainedPattern:
#     patterns: Sequence[ASTNode] | ASTNode       # TODO Why plural, i.e., patterns?
#     eligible: Callable[[PatternMatch], bool]
#
#
# class MatchFinder:
#
#     DEFAULT_EXCLUDE_KIND = "comment"
#
#     @staticmethod
#     def find_all(
#         src_nodes: Sequence[ASTNode] | ASTNode,
#         *patterns_list: Sequence[ASTNode] | ConstrainedPattern,
#         recursive: bool = True,
#         exclude_kind: str = DEFAULT_EXCLUDE_KIND,
#         part_of_translation_unit: bool = True,
#     ) -> Stream[PatternMatch]:
#         return MatchFinder.find_all_strict(
#             src_nodes,
#             patterns_list,
#             recursive=recursive,
#             exclude_kind=exclude_kind,
#             part_of_translation_unit=part_of_translation_unit,
#         )
#
#     #TODO: Why don't we define types for X | Sequence[X]?
#     #TODO: Why don't we enforce that input is always a sequence of ASTNodes (so just use [] around a single ASTNode)?
#     #TODO: Why don't we define a type for a pattern: Sequence[ASTNode] | ConstrainedPattern
#     #TODO: Why don't we introduce a Pattern class (with multiple constructors for the different cases)?
#
#     #TODO: why is the type of patterns_list different from find_all (directly above)?
#     @staticmethod
#     def find_all_strict(
#         src_nodes: Sequence[ASTNode] | ASTNode,
#         patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
#         recursive: bool = True,
#         exclude_kind: str = DEFAULT_EXCLUDE_KIND,
#         part_of_translation_unit: bool = True,
#     ) -> Stream[PatternMatch]:
#         """
#         Finds all pattern matches in the given source nodes.
#
#         Args:
#             src_nodes (Sequence[ASTNode] | ASTNode): The source nodes to search within. Can be a single ASTNode or a list of ASTNodes.
#             *patterns_list (Sequence[ASTNode]): One or more lists of ASTNodes representing the patterns to match.
#             recursive (bool, optional): Whether to search recursively within the source nodes. Defaults to True.
#             exclude_kind (type, optional): The kind of nodes to exclude from the search. Defaults to DEFAULT_EXCLUDE_KIND.
#
#         Returns:
#             Stream[PatternMatch]: A stream of pattern matches found in the source nodes.
#         """
#         if not isinstance(src_nodes, Sequence):
#             src_nodes = [src_nodes]
#
#         def src_filter(nodes: Sequence[ASTNode]):
#             if not part_of_translation_unit:
#                 return MatchUtils.exclude_nodes_by_kind(exclude_kind, nodes)
#             return [
#                 node
#                 for node in MatchUtils.exclude_nodes_by_kind_as_sequence(
#                     exclude_kind, nodes
#                 )
#                 if node.is_part_of_translation_unit()
#             ]
#
#         return Stream(
#             MatchFinder.__find_all(
#                 src_nodes, patterns_list, recursive=recursive, src_filter=src_filter
#             )
#         )
#
#     @staticmethod
#     def match_pattern(
#         src_nodes: Sequence[ASTNode] | ASTNode,
#         patterns: Sequence[ASTNode] | ConstrainedPattern,
#         src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]] = lambda n: n,
#     ) -> Optional[PatternMatch]:
#         """
#         Matches a given source node or list of source nodes against a list of pattern nodes.
#
#         Args:
#             src_nodes (Sequence[ASTNode] | ASTNode): The source node or list of source nodes to be matched.
#             patterns (Sequence[ASTNode]): The list of pattern nodes to match against the source nodes.
#             src_filter: The kind of nodes to exclude from matching.
#
#         Returns:
#             Optional[PatternMatch]: A PatternMatch object if a match is found, otherwise None.
#         """
#         eligible: Callable[[PatternMatch], bool] = lambda _: True
#         if isinstance(src_nodes, ASTNode):
#             src_nodes = [src_nodes]
#         if isinstance(patterns, ConstrainedPattern):
#             eligible = patterns.eligible
#             patterns = (
#                 patterns.patterns
#                 if isinstance(patterns.patterns, Sequence)
#                 else [patterns.patterns]
#             )
#         if isinstance(patterns, ASTNode):
#             patterns = [patterns]
#         patterns = src_filter(patterns)  # exclude nodes by kind
#         keys = MatchUtils.get_multi_wildcard_keys(patterns)
#         multiplicity = {key: 0 for key, count in Counter(keys).items() if count > 1}
#         # remove the last item from multiplicity because it the last item is already greedy
#         if len(multiplicity) > 1:
#             multiplicity.popitem()
#         has_next_multiplicity = True
#         while has_next_multiplicity:
#             pattern_match = MatchFinder.__match_pattern(
#                 src_nodes, patterns, 0, multiplicity, None, src_filter=src_filter
#             )
#             if pattern_match and eligible(pattern_match):
#                 return pattern_match
#             has_next_multiplicity = MatchUtils.next_multiplicity(multiplicity)
#         return None
#
#     @staticmethod
#     def is_match(
#         src1: ASTNode | Sequence[ASTNode],
#         src2: ASTNode | Sequence[ASTNode],
#         src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]] = lambda n: n,
#     ) -> bool:
#         if isinstance(src2, ASTNode):
#             src2 = [src2]
#         return MatchFinder.match_pattern(src1, src2, src_filter=src_filter) is not None
#
#     @staticmethod
#     def find_all_py(
#         src_nodes: Sequence[ASTNode],
#         pattern: ASTNode
#     ) -> Iterator[PatternMatch]:
#         target_nodes = src_nodes
#         while target_nodes:
#             pattern_match = MatchFinder.match_pattern(target_nodes, pattern)
#             if pattern_match:
#                 break  # only one match is needed
#
#             if pattern_match:
#                 target_nodes = pattern_match._get_remaining_nodes()
#                 yield pattern_match
#             else:
#                 target_nodes = target_nodes[1:]  # skip the first node
#             for node in src_nodes:
#                 children = node.get_children()
#                 yield from MatchFinder.__find_all(children,pattern )
#     @staticmethod
#     def __find_all(
#         src_nodes: Sequence[ASTNode],
#         patterns_list: Sequence[Sequence[ASTNode] | ConstrainedPattern],
#         recursive: bool,
#         src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]],
#     ) -> Iterator[PatternMatch]:
#         src_nodes = src_filter(
#             src_nodes
#         )  # exclude nodes by kind and optionally is part of translation unit
#         target_nodes = src_nodes
#
#         while target_nodes:
#             pattern_match = None
#             for patterns in patterns_list:
#                 pattern_match = MatchFinder.match_pattern(
#                     target_nodes, patterns, src_filter
#                 )
#                 if pattern_match:
#                     break  # only one match is needed
#
#             if pattern_match:
#                 target_nodes = pattern_match._get_remaining_nodes()
#                 if VERBOSE:
#                     do_log(0, "VALID MATCH FOUND")
#                 yield pattern_match
#             else:
#                 target_nodes = target_nodes[1:]  # skip the first node
#         # recursively evaluate all children
#         if recursive:
#             for node in src_nodes:
#                 children = node.get_children()
#                 if children:
#                     yield from MatchFinder.__find_all(
#                         children,
#                         patterns_list,
#                         recursive=recursive,
#                         src_filter=src_filter,
#                     )
#
#     @staticmethod
#     def __match_pattern(
#         src_nodes: Sequence[ASTNode],
#         patterns: Sequence[ASTNode],
#         depth: int,
#         multiplicity: dict[str, int],
#         pattern_match: Optional[PatternMatch],
#         src_filter: Callable[[Sequence[ASTNode]], Sequence[ASTNode]],
#     ) -> Optional[PatternMatch]:
#         if pattern_match is None:
#             pattern_match = PatternMatch(src_nodes, patterns)
#
#         indent = depth * 4  # for logging purposes only
#
#         only_multi_wild_cards = all(MatchUtils.is_multi_wildcard(p) for p in patterns)
#         # if there are no patterns left or only multi wildcards left and no source nodes, return the current match
#         if len(patterns) == 0 or (only_multi_wild_cards and len(src_nodes) == 0):
#             # only allow remaining srcNodes is this is the root level, depicted by depth == 0
#             if len(src_nodes) > 0 and depth > 0:
#                 return None
#             # we might end up with a multi wildcard at the end of the pattern list and no srcNodes left so add it
#             if only_multi_wild_cards and len(patterns) == 1:
#                 pattern_match._query_create(patterns[0].get_name())
#
#             if MatchValidation.validate(pattern_match._key_matches):
#                 # srcNodes that are not (yet) matched are stored in the pattern match
#                 pattern_match._set_remaining_nodes(src_nodes)
#                 # remove the non-matching from the source nodes
#                 pattern_match.src_nodes = [
#                     n for n in pattern_match.src_nodes if n not in src_nodes
#                 ]
#                 return pattern_match
#             return None
#
#         # if patterns left but no source nodes, return None
#         if len(src_nodes) == 0:
#             return None
#
#         src_node = src_nodes[0]
#         pattern_node = patterns[0]
#
#         if VERBOSE:
#             do_log(
#                 indent,
#                 "\n** CHECKING **",
#                 src_node.get_text(),
#                 "** AGAINST **",
#                 pattern_node.get_text(),
#                 "\n",
#             )
#
#         if MatchUtils.is_multi_wildcard(pattern_node):
#             wildcard_match = pattern_match._query_create(pattern_node.get_name())
#             greediness = multiplicity.get(pattern_node.get_name(), 0)
#             if greediness <= len(wildcard_match.nodes) and len(patterns) > 1:
#                 # multiplicity of multi-wildcards is 0 so first try to match the next pattern with the current srcNodes
#                 # a clone is needed to keep the current state of the match when the next match fails
#
#                 next_match = MatchFinder.__match_pattern(
#                     src_nodes,
#                     patterns[1:],
#                     depth,
#                     multiplicity,
#                     pattern_match.clone(),
#                     src_filter,
#                 )
#                 if next_match:
#                     return next_match
#             wildcard_match._add_node(src_node)
#
#             if VERBOSE:
#                 do_log(
#                     indent,
#                     "** $$WILDCARD **",
#                     pattern_node.get_text(),
#                     "** MATCHES **",
#                     raw(wildcard_match.nodes),
#                 )
#             return MatchFinder.__match_pattern(
#                 src_nodes[1:], patterns, depth, multiplicity, pattern_match, src_filter
#             )
#         elif MatchUtils.is_single_wildcard(pattern_node) or MatchUtils.is_match(
#             src_node, pattern_node
#         ):
#             if pattern_node.is_statement() and not src_node.is_statement():  # type: ignore
#                 return None
#             # if the pattern node has children then kind must match (to distinct for instance while and if)
#             if pattern_node.get_children() and (
#                 not MatchUtils._is_wildcard_match(src_node, pattern_node)
#             ):
#                 return None
#
#             if MatchUtils.is_single_wildcard(pattern_node):
#                 wildcard_match = pattern_match._query_create(pattern_node.get_name())
#                 # TODO check with pierre whether we should take the highest or the deepest match
#                 # if not  wildcard_match.nodes:
#                 wildcard_match._add_node(src_node)
#             else:
#                 # store the exact match because it might be needed to determine the location of a multi wildcard match without nodes
#                 pattern_match._query_create(MatchUtils.EXACT_MATCH)._add_node(src_node)
#             if VERBOSE:
#                 do_log(
#                     indent,
#                     pattern_node.get_text(),
#                     "** MATCHES **",
#                     src_node.get_text(),
#                 )
#
#             # the current match is found if the current pattern and src node match and their children match
#             if pattern_node.get_children():
#                 src_child_nodes = src_filter(src_node.get_children())
#                 pattern_child_nodes = src_filter(pattern_node.get_children())
#                 found_match = MatchFinder.__match_pattern(
#                     src_child_nodes,
#                     pattern_child_nodes,
#                     depth + 1,
#                     multiplicity,
#                     pattern_match,
#                     src_filter,
#                 )
#                 if not found_match:
#                     return None
#                 pattern_match = (
#                     found_match  # update the pattern match with the result of the child
#                 )
#             # invariant: a match is found if the current pattern and src node match and their successors match
#             return MatchFinder.__match_pattern(
#                 src_nodes[1:],
#                 patterns[1:],
#                 depth,
#                 multiplicity,
#                 pattern_match,
#                 src_filter,
#             )
#         return None
#
#
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
#
# def do_log(indent: int, *msgs: str):
#     text = "\n".join(msgs)
#     print(" ".join(f'{" "*indent}{l}' for l in text.splitlines()))
#
#
# def raw(nodes: Sequence[ASTNode]):
#     return " ".join([n.get_text() for n in nodes])
