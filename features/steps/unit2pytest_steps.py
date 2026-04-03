import pytest

from hamcrest import assert_that, contains_string, not_, raises, is_not, calling
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl.python import PythonRstNode
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTFactory


class Ast:
    def __init__(self):
        self.file = ""
        self.atu = None
        self.signature = None


@pytest.fixture
def context():
    return Ast


@scenario("../convert-unit-to-pytest.feature", "convert unittest to pytest")
def test_convert_unit_to_pytest():
    pass


@given(parsers.parse("'{file}' file"))
def step_given_file(context, file):
    context.file = file
    context.factory = ASTFactory(PythonRstNode, [])
    context.atu = context.factory.create(file)


@given(parsers.parse("it contains '{statement}'"))
@then(parsers.parse("it should contain '{statement}'"))
def step_given_contains(context, statement):
    source = context.atu.signature
    assert_that(source, contains_string(statement), f"Expected '{statement}' in source")


@given("an AST extracted from that source file without errors")
@then("AST extracted from that conversion should without errors")
def step_given_ast_no_errors(context):
    assert_that(
        calling(context.atu.translation_unit.check_diagnostics),
        is_not(raises(Exception)),
    )


@when("I convert it to pytest")
def step_when_convert(context):
    converter = Unit2Pytest(context.file)
    converter.run()
    context.atu = context.factory.create(context.file)


@then(parsers.parse("it should not contain '{statement}'"))
def step_then_not_contain(context, statement):
    source = context.atu.signature
    assert_that(source, not_(contains_string(statement)))
