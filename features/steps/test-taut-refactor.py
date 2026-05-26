from renaissance.refactoring.taut2pyunit import Taut2Pyunit
from steps.test_steps import *
from pytest_bdd import when, scenario


@scenario("refactor-taut-test.feature", "migrate taut to unittest without syntax errors", " utf-8", "..")
def test_taut_test():
    pass


@when("I convert taut to unittest")
def step_when_convert(context):
    converter = Taut2Pyunit(context.file)
    converter.in_memory = True
    converter.run()
    context.atu = context.factory.create(context.file)
    context.signature = converter.apply_to_string()
