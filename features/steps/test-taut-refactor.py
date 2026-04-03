import pytest
from pytest_bdd import given, when, then, scenario, parsers
from renaissance.impl.python import PythonRstNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, ASTRewriter, MatchFinder
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.refactor_utils import fix_indent


@pytest.fixture
def context():
    return {}


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


@given("'python' programming language")
def init_language_factory(context):
    context["factory"] = ASTFactory(PythonRstNode, "")


@given(parsers.parse("'{file}' file written in that programming language"))
def step_impl(context, file):
    context["atu"] = context["factory"].create(file)


@given("an AST extracted from that source file without errors")
def step_impl(context):
    assert not context["atu"].translation_unit.check_diagnostics()


@given(parsers.parse("node '{old}' exits within that AST"))
def step_impl(context, old):
    pattern_factory = PythonPatternFactory(context["factory"], context["atu"])
    find = pattern_factory.create_statements(old)
    context["result"] = match_pattern(context["atu"].children, find)[0]
    assert context["result"]


@when("that node is removed")
def step_impl(context):
    context["rewriter"] = ASTRewriter(context["atu"])
    context["rewriter"].remove(context["result"].nodes)


@when("rewrites replace is performed on that sequence of descendant nodes")
def step_impl(context):
    context["rewriter"].apply()


@then("in the modified source file that node is removed")
def step_impl(context):
    assert "import TAUT" not in context["rewriter"].apply_to_string()


@when(parsers.parse("that node is replaced by '{replacement}'"))
def step_impl(context, replacement):
    context["replacement"] = replacement
    context["rewriter"] = ASTRewriter(context["atu"])
    context["rewriter"].replace(replacement, context["result"].nodes)


@then("in the modified source file that node is replaced by the given text")
def step_impl(context):
    assert context["replacement"] in context["rewriter"].apply_to_string()


@when("run flake8 and autopep8 to auto fix the code")
def step_impl(context):
    context["fixed_code"] = fix_indent(context["rewriter"].apply_to_string())
