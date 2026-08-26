from pathlib import Path

from pytest_bdd import scenario, when

from renaissance.refactoring.taut2pyunit import Taut2Pyunit
from steps.conftest import FEATURES_BASE_DIR


@scenario(
    "refactor-taut-test.feature",
    "migrate taut to unittest without syntax errors",
    encoding="utf-8",
    features_base_dir=str(FEATURES_BASE_DIR)
)
def test_taut_test():
    pass


@when("I convert taut to unittest")
def step_when_convert(context):
    converter = Taut2Pyunit(context.file)
    converter.in_memory = True
    converter.run()
    context.atu = context.factory.create(context.file)
    context.signature = converter.apply_to_string()
    Path(converter.get_migrated_path(context.file)).unlink(missing_ok=True)
