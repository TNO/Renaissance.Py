"""AI: Step definitions for the refactor-taut-test BDD feature scenario."""

from pathlib import Path

from pytest_bdd import scenario, when

from renaissance.recipes.taut_to_python_unittest import TautToPythonUnittest
from steps.conftest import FEATURES_BASE_DIR


@scenario(
    "refactor-taut-test.feature",
    "migrate taut to unittest without syntax errors",
    encoding="utf-8",
    features_base_dir=str(FEATURES_BASE_DIR),
)
def test_taut_test():
    """AI: Scenario test for the 'migrate taut to unittest without syntax errors' scenario."""


@when("I convert taut to unittest")
def step_when_convert(context):
    """AI: Convert the scenario's taut test file to a Python unittest and record its output."""
    converter = TautToPythonUnittest(context.file)
    converter.in_memory = True
    converter.run()
    context.atu = context.factory.create(context.file)
    context.signature = converter.apply_to_string()
    Path(converter.get_migrated_path(context.file)).unlink(missing_ok=True)
