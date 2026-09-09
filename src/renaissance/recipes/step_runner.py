"""A small, generic way to sequence independently-committable fix actions across one or more recipes."""

from collections.abc import Callable, Sequence  # noqa: TC003
from dataclasses import dataclass

from renaissance.recipes.python_refactoring import PythonRefactoring  # noqa: TC001


@dataclass(frozen=True)
class Step:
    """One independently-runnable, independently-committable fix action."""

    label: str
    recipe: PythonRefactoring
    action: Callable[[], dict[str, str]]


def run_steps(steps: Sequence[Step]) -> dict[str, dict[str, str]]:
    """Run each step in order, committing its recipe if the step fixed anything.

    Returns {step.label: {name: "fixed" | "unsafe"}}, one entry per step, in step order.
    """
    result: dict[str, dict[str, str]] = {}
    for step in steps:
        outcome = step.action()
        if "fixed" in outcome.values():
            step.recipe.commit()
        result[step.label] = outcome
    return result
