import pytest
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl.python.factory import PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTFactory, ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern


@pytest.fixture
def context():
    return {}


@scenario("../refactor-python-file.feature", "python code")
def test_refactor_python_file():
    pass


@given("'python' programming language")
def init_language_factory(context):
    context["factory"] = ASTFactory(PythonRstNode, "")


@given(parsers.parse("'{file}' file written in that programming language"))
def step_impl(context, file):
    context["atu"] = context["factory"].create(file)


@given(parsers.parse("node '{old}' exits within that AST"))
def step_impl(context, old):
    pattern_factory = PythonPatternFactory(context["factory"], context["atu"])
    find = pattern_factory.create_statements(old)
    context["result"] = match_pattern(context["atu"].children, find)
    assert context["result"]


@given("a sequence of descendant nodes of that node")
def step_impl(context):
    assert context["result"][0].nodes[0].children


@when(parsers.parse("that node is replaced by '{replacement}'"))
def step_impl(context, replacement):
    context["replacement"] = replacement
    context["rewriter"] = ASTRewriter(context["atu"])
    context["rewriter"].replace(replacement, context["result"][0].nodes)


@when("rewrites replace is performed on that sequence of descendant nodes")
def step_impl(context):
    context["rewriter"].apply()


@then("in the modified source file that node is replaced by the given text")
def step_impl(context):
    assert context["replacement"] in context["rewriter"].apply_to_string()


@then("all rewrites on that sequence of descendant nodes are not performed or hidden")
def step_impl(context):
    assert context["rewriter"].has_changed()
