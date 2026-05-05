import pytest
from hamcrest import has_length, greater_than_or_equal_to
from hamcrest.core import assert_that

from renaissance.impl.python.factory import PythonFactory,PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree.match_finder import find_variants

code = """
f(0,0)
"""

PLACEHOLDER_BEFORE: str = "$$before"
PLACEHOLDER_AFTER: str = "$$after"
PATTERN_CALL: str = "f(" + PLACEHOLDER_BEFORE + ", 0, " + PLACEHOLDER_AFTER + ")"


class TestMatchFinderMultiAssignments:
    @pytest.mark.skip("not impl. yet")
    def test_find_multi_assignments(self):
        # set up
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text(code)
        pattern = PythonPatternFactory(factory).create_statements(PATTERN_CALL)

        # execute
        variants = list(find_variants(atu.children, pattern))  # Use list, since we want to access its content multiple times

        # verify
        assert_that(variants, has_length(2), f"Two matches expected, got {len(variants)}.")
        # TODO Discuss what behaviour do we exactly want?
        # In this case, 1 match on the AST node "f(0,0)" with 2 assignments (as checked below) is also acceptable to me.

        expected: set[frozenset[tuple[str, str]]] = {
            frozenset({PLACEHOLDER_BEFORE: "", PLACEHOLDER_AFTER: "0"}.items()),
            frozenset({PLACEHOLDER_BEFORE: "0", PLACEHOLDER_AFTER: ""}.items()),
        }

        actual: set[frozenset[tuple[str, str]]] = set()
        for vatiant in variants:
            # TODO getting the location of a (possibly empty) multiple placeholder is no longer supported
            before_location = vatiant.locations[PLACEHOLDER_BEFORE]
            after_location = vatiant.locations[PLACEHOLDER_AFTER]

            assignment: dict[str, str] = {}
            assignment[PLACEHOLDER_BEFORE] = atu.translation_unit.content[before_location.offset : before_location.end_offset]
            assignment[PLACEHOLDER_AFTER] = atu.translation_unit.content[after_location.offset : after_location.end_offset]

            actual.add(frozenset(assignment.items()))
        assert expected == actual, "Unexpected assignments of placeholders"
