import itertools
from typing import Callable, Sequence
from hamcrest import assert_that, equal_to
import pytest
from _pytest.mark.structures import ParameterSet
from renaissance.syntax_tree.match_finder import is_match


def make_parametersets_of_equivalence_classes(
    classes: Sequence[Sequence[str]],
) -> list[ParameterSet]:
    """
    Expand equivalence classes of string literals into independent test cases.

    Generates:
      - expect_equal=True for all pairs within each class (combinations)
      - expect_equal=False for all pairs across different classes (cartesian products)
    """
    params: list[ParameterSet] = []

    indexed = list(enumerate(classes))
    # Within-class: all combinations must be equivalent
    for ci, cls in indexed:
        for a, b in itertools.combinations(cls, 2):
            params.append(pytest.param(a, b, True, id=f"eq:c{ci}:{a}=={b}"))

    # Across-classes: all cross-products must be not equivalent
    for (ci, cls_i), (cj, cls_j) in itertools.combinations(indexed, 2):
        for a, b in itertools.product(cls_i, cls_j):
            params.append(pytest.param(a, b, False, id=f"ne:c{ci}!=c{cj}:{a}!={b}"))

    return params


def assert_pair_equivalence[TNode](to_ast: Callable[[str], TNode], a_txt: str, b_txt: str, expected: bool) -> None:
    """
    Convert to texts to AST and assert the expected (in)equivalence.
    """
    a_node = to_ast(a_txt)
    b_node = to_ast(b_txt)

    assert_that(is_match(a_node, b_node), equal_to(expected), f"matching {a_txt} and {b_txt} doesn't result in {expected}.")


    