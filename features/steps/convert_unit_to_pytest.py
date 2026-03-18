import pytest
from RestrictedPython.Guards import raise_
from hamcrest import assert_that, is_in, calling, raises, is_not, contains_string
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl.python import PythonASTNode
from renaissance.refactoring.unit2pytest import Unit2PyTest
from renaissance.syntax_tree import ASTFactory


@pytest.fixture
def context():
    return {}


@scenario('../convert-unit-to-pytest.feature', 'convert unittest to pytest')
def test_convert_unit_to_pytest():
    pass


@given(parsers.parse("'{file}' file"))
def step_given_file(context, file):
    context["file"] = file
    context["factory"] = ASTFactory(PythonASTNode, [])
    context["atu"] = context["factory"].create(file)


@given(parsers.parse("it contains '{statement}'"))
def step_given_contains(context, statement):
    source = context["atu"].signature
    assert_that(source, contains_string(statement), f"Expected '{statement}' in source")


@given("an AST extracted from that source file without errors")
@then("AST extracted from that conversion should without errors")
def step_given_ast_no_errors(context):
    assert_that(calling(context["atu"].translation_unit.check_diagnostics), is_not(raises(Exception)))

@when("I convert it to pytest")
def step_when_convert(context):
    converter = Unit2PyTest(context["file"])
    converter.convert_pytest()
    context["converted_atu"] = context["factory"].create(context["file"])



@then(parsers.parse("it should not contain '{statement}'"))
def step_then_not_contain(context, statement):
    source = context["converted_atu"].translation_unit.text
    assert statement not in source, f"Expected '{statement}' to not be in converted source"
    assert_that(statement,  not(is_in(source)), f"Expected '{statement}' in source")

