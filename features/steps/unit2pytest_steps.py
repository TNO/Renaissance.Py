from .test_steps import *
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl.python import PythonRstNode
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTFactory

@scenario("../convert-unit-to-pytest.feature", "convert unittest to pytest")
def test_convert_unit_to_pytest():
    pass

@when("I convert it to pytest")
def step_when_convert(context):
    converter = Unit2Pytest(context.file)
    converter.run()
    context.atu = context.factory.create(context.file)
