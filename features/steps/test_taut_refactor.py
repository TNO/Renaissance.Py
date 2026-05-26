from pytest_bdd import when, scenario

from features.steps.conftest import FEATURES_BASE_DIR
from renaissance.refactoring.taut2pyunit import Taut2Pyunit


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
