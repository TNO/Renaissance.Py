"""Tests for Step/run_steps."""

from collections.abc import Callable  # noqa: TC003

import pytest
from hamcrest import assert_that, equal_to, is_
from pytest_mock import MockerFixture  # noqa: TC002

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.step_runner import Step, run_steps


class TestRunSteps:
    """See module docstring."""

    def test_collects_each_steps_result_under_its_own_label_in_order(self, mocker: MockerFixture) -> None:
        recipe = mocker.Mock(spec=PythonRefactoring)
        steps = [
            Step("first", recipe, lambda: {"A": "fixed"}),
            Step("second", recipe, lambda: {"B": "unsafe"}),
        ]

        result = run_steps(steps)

        assert_that(result, equal_to({"first": {"A": "fixed"}, "second": {"B": "unsafe"}}))
        assert_that(list(result.keys()), equal_to(["first", "second"]))

    @pytest.mark.parametrize(
        ("action_result", "expect_commit"),
        [
            ({"A": "fixed"}, True),
            ({"A": "unsafe"}, False),
            ({}, False),
            ({"A": "fixed", "B": "unsafe"}, True),
        ],
    )
    def test_commits_only_when_a_step_fixed_something(
        self,
        mocker: MockerFixture,
        action_result: dict[str, str],
        expect_commit: bool,  # noqa: FBT001
    ) -> None:
        recipe = mocker.Mock(spec=PythonRefactoring)
        action: Callable[[], dict[str, str]] = lambda: action_result  # noqa: E731

        run_steps([Step("only", recipe, action)])

        assert_that(recipe.commit.called, is_(expect_commit))

    def test_each_steps_recipe_commits_independently(self, mocker: MockerFixture) -> None:
        fixing_recipe = mocker.Mock(spec=PythonRefactoring)
        unsafe_recipe = mocker.Mock(spec=PythonRefactoring)

        run_steps([
            Step("fixes", fixing_recipe, lambda: {"A": "fixed"}),
            Step("unsafe", unsafe_recipe, lambda: {"B": "unsafe"}),
        ])

        assert_that(fixing_recipe.commit.called, is_(True))
        assert_that(unsafe_recipe.commit.called, is_(False))
