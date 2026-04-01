from renaissance.impl.python.python_ast_node import PythonASTNode
from renaissance.impl.python.python_pattern_factory import PythonPatternFactory
from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.match_finder import find_all

code = """
def f(x,y):
    skip

def g():
    f(0,0)
"""

PLACEHOLDER_BEFORE: str = "$$before"
PLACEHOLDER_AFTER: str = "$$after"
PATTERN_CALL: str = "f(" + PLACEHOLDER_BEFORE + ", 0, " + PLACEHOLDER_AFTER + ")"


class TestMatchFinderMultiAssignments:

    def test_find_multi_assignments(self):
        # set up
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text(code, "temp.py")
        pattern = PythonPatternFactory(factory).create_expression(PATTERN_CALL)

        # execute
        matches = list(find_all([atu], [pattern]))  # Use list, since we want to access its content multiple times

        # verify
        assert 2 == len(matches), f"Two matches expected, got {len(matches)}."
        # TODO Discuss what behaviour do we exactly want?
        # In this case, 1 match on the AST node "f(0,0)" with 2 assignments (as checked below) is also acceptable to me.

        expected: set[frozenset[tuple[str, str]]] = {
            frozenset({PLACEHOLDER_BEFORE: "", PLACEHOLDER_AFTER: "0"}.items()),
            frozenset({PLACEHOLDER_BEFORE: "0", PLACEHOLDER_AFTER: ""}.items()),
        }

        actual: set[frozenset[tuple[str, str]]] = set()
        for match in matches:
            # TODO getting the location of a (possibly empty) multiple placeholder is no longer supported
            before_location = match.locations[PLACEHOLDER_BEFORE]
            after_location = match.locations[PLACEHOLDER_AFTER]

            assignment: dict[str, str] = {}
            assignment[PLACEHOLDER_BEFORE] = atu.translation_unit.content[before_location.offset : before_location.end_offset]
            assignment[PLACEHOLDER_AFTER] = atu.translation_unit.content[after_location.offset : after_location.end_offset]

            actual.add(frozenset(assignment.items()))
        assert expected == actual, "Unexpected assignments of placeholders"
