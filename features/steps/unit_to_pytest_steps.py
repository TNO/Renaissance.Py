"""AI: Step definitions for the convert-unit-to-pytest BDD feature scenario."""

from pytest_bdd import scenario, when

from renaissance.recipes.unit_to_pytest import UnitToPytest
from steps.test_steps import *  # noqa: F403 -- pytest-bdd step aggregation


@scenario("convert-unit-to-pytest.feature", "convert unittest to pytest", "utf-8", "..")
def test_convert_unit_to_pytest():
    """AI: Scenario test for the 'convert unittest to pytest' scenario."""


@when("I convert it to pytest")
def step_when_convert(context):
    """AI: Convert the scenario's unittest file to pytest and re-parse it."""
    converter = UnitToPytest(context.file)
    converter.run()
    context.atu = context.factory.create(context.file)
