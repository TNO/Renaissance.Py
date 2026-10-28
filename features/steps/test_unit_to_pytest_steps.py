# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Step definitions for the convert-unit-to-pytest BDD feature scenario."""

from pytest_bdd import scenario, when

from renaissance.recipes.unit_to_pytest import UnitToPytest
from steps.conftest import FEATURES_BASE_DIR


@scenario(
    "convert-unit-to-pytest.feature",
    "convert unittest to pytest",
    encoding="utf-8",
    features_base_dir=str(FEATURES_BASE_DIR),
)
def test_convert_unit_to_pytest() -> None:
    """AI: Scenario test for the 'convert unittest to pytest' scenario."""


@when("I convert it to pytest")
def step_when_convert(context) -> None:
    """AI: Convert the scenario's unittest file to pytest in memory and re-parse the result."""
    converter = UnitToPytest(context.file)
    converter.in_memory = True
    converter.run()
    context.signature = converter.apply_to_string()
    context.atu = context.factory.create_from_text(context.signature, context.file)
