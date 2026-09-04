from pytest_bdd import scenario, when

from renaissance.recipes.unit2pytest import Unit2Pytest
from steps.test_steps import *


@scenario("convert-unit-to-pytest.feature", "convert unittest to pytest", "utf-8", "..")
def test_convert_unit_to_pytest():
    pass


@when("I convert it to pytest")
def step_when_convert(context):
    converter = Unit2Pytest(context.file)
    converter.run()
    context.atu = context.factory.create(context.file)
