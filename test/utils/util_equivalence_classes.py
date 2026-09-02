"""Util functions for equivalence class testing of AstProtocol nodes."""

import itertools
from collections.abc import Callable, Sequence

import pytest
from _pytest.mark.structures import ParameterSet
from hamcrest import assert_that, equal_to

from renaissance.syntax_tree.match_finder import AstProtocol, is_match


def escape_new_lines(txt: str) -> str:
    """Escape new line characters in a string."""
    return txt.replace("\n", "\\n")


def make_parametersets_of_equivalence_classes(
    info: str,
    parse: Callable[[str], AstProtocol | Sequence[AstProtocol]],
    equiv_classes: Sequence[Sequence[str]],
) -> list[ParameterSet]:
    """Expand equivalence classes into independent test cases.

    Generates:
      - expect_equal=True for all pairs within each class (combinations)
      - expect_equal=False for all pairs across different classes (cartesian products)
    """
    # make data structure of indices and parsed strings
    data = list(
        enumerate([[(ti, txt, parse(txt)) for ti, txt in enumerate(equiv_class)] for equiv_class in equiv_classes]),
    )

    # make parameters for tests
    params: list[ParameterSet] = []
    # Within-class: all combinations must be equivalent
    for ci, cls in data:
        for (ai, at, ap), (bi, bt, bp) in itertools.combinations(cls, 2):
            params.append(
                pytest.param(
                    ap,
                    bp,
                    True,
                    id=f'{info} - c[{ci}][{ai}] eq c[{ci}][{bi}] : "{escape_new_lines(at)}" == "{escape_new_lines(bt)}"',
                ),
            )

    # Across-classes: all cross-products must be not equivalent
    for (ci, cls_i), (cj, cls_j) in itertools.combinations(data, 2):
        for (ai, at, ap), (bj, bt, bp) in itertools.product(cls_i, cls_j):
            params.append(
                pytest.param(
                    ap,
                    bp,
                    False,
                    id=f'{info} - c[{ci}][{ai}] ne c[{cj}][{bj}] : "{escape_new_lines(at)}" != "{escape_new_lines(bt)}"',
                ),
            )

    return params


def assert_pair_equivalence(
    a: AstProtocol | Sequence[AstProtocol],
    b: AstProtocol | Sequence[AstProtocol],
    expected: bool,
) -> None:
    """Assert the expected (in)equivalence of a pair of nodes (AstProtocol)."""
    match (isinstance(a, Sequence), isinstance(b, Sequence)):
        case (True, True):
            assert isinstance(a, Sequence) and isinstance(b, Sequence)
            la = list(a)
            lb = list(b)
            actual = (len(la) == len(lb)) and all(is_match(ea, eb) for ea, eb in zip(la, lb, strict=False))
            assert_that(actual, equal_to(expected), f"matching {a} and {b} doesn't result in {expected}.")
        case (False, False):
            assert_that(is_match(a, b), equal_to(expected), f"matching {a} and {b} doesn't result in {expected}.")
        case _:
            assert_that(False, equal_to(expected), f"matching {a} and {b} doesn't result in {expected}.")
