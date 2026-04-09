import pytest
from hamcrest import assert_that, calling, is_not, raises, contains_string, not_
from pytest_bdd import given, when, then, scenario, parsers
from renaissance.impl.python import PythonRstNode
from renaissance.impl.python.factory import PythonFactory

class Ast:
    def __init__(self):
        self.file = ""
        self.atu = None
        self.signature = None

@pytest.fixture
def context():
    return Ast()

@given(parsers.parse("'{file}' file"))
def step_given_file(context, file):
    context.file = file
    context.factory = PythonFactory(PythonRstNode)
    context.atu = context.factory.create(file)
    context.signature = context.atu.signature

@given(parsers.parse("it contains '{statement}'"))
@then(parsers.parse("it should contain '{statement}'"))
def step_given_contains(context, statement):
    statement = statement.replace("\\n", "\n")
    assert_that(context.signature, contains_string(statement), f"Expected '{statement}' in source")

@given("an AST extracted from that source file without errors")
@then("AST extracted from that conversion should without errors")
def step_given_ast_no_errors(context):
    assert_that(
        calling(context.atu.translation_unit.check_diagnostics),
        is_not(raises(Exception)),
    )

@then(parsers.parse("it should not contain '{statement}'"))
def step_then_not_contain(context, statement):
    assert_that(context.signature, not_(contains_string(statement)))