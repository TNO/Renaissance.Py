import pytest
from hamcrest import assert_that, calling, is_not, raises, contains_string, not_
from pytest_bdd import given, when, then, scenario, parsers
from renaissance.impl.python import PythonRstNode, PythonPatternFactory
from renaissance.impl.python.factory import PythonFactory
from renaissance.refactoring.taut2pyunit import Taut2Pyunit
from renaissance.syntax_tree import ASTFactory, ASTRewriter, MatchFinder
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.refactor_utils import fix_indent

class Ast:
    def __init__(self):
        self.file = ""
        self.atu = None
        self.signature = None

@pytest.fixture
def context():
    return Ast


@scenario("../refactor-taut-test.feature", "remove import")
def test_taut_test():
    pass


@scenario("../refactor-taut-test.feature", "replace taut")
def test_taut_test2():
    pass


@scenario("../refactor-taut-test.feature", "replace import")
def test_taut_test3():
    pass


@scenario("../refactor-taut-test.feature", "remove decorator")
def test_taut_test4():
    pass


@scenario("../refactor-taut-test.feature", "replace TestDoubles")
def test_taut_test5():
    pass

@scenario("../refactor-taut-test.feature", "convert setUp")
def test_taut_test6():
    pass

@scenario("../refactor-taut-test.feature", "convert tearDown")
def test_taut_test7():
    pass

@scenario("../refactor-taut-test.feature", "convert setUpCommon")
def test_taut_test8():
    pass

@scenario("../refactor-taut-test.feature", "convert tearDownCommon")
def test_taut_test9():
    pass

@given(parsers.parse("'{file}' file"))
def step_given_file(context, file):
    context.file = file
    context.factory = PythonFactory(PythonRstNode)
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

@when("I convert taut to unittest")
def step_when_convert(context):
    converter = Taut2Pyunit(context.file)
    converter.run()
    context.atu = context.factory.create(context.file)


@then(parsers.parse("it should not contain '{statement}'"))
def step_then_not_contain(context, statement):
    source = context.atu.signature
    assert_that(source, not_(contains_string(statement)))