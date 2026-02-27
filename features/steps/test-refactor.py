import pytest
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder, ASTRewriter


@pytest.fixture
def context():
    return {
            }
@scenario('../refactor-python-file.feature','python code')
def test_refactor_python_file():
    pass

@given("'python' programming language")
def init_language_factory(context):
    context["factory"] = ASTFactory(PythonASTNode, '')


@given(parsers.parse("'{file}' file written in that programming language"))
def step_impl(context, file):
    context["atu"] = context["factory"].create(file)

@given("an AST extracted from that source file without errors")
def step_impl(context):
    assert not context["atu"].translation_unit.check_diagnostics()


@given(parsers.parse("node '{old}' exits within that AST"))
def step_impl(context, old):
    pattern_factory = PythonPatternFactory(context['factory'], context['atu'])
    find = pattern_factory.create_statements(old)
    context['result'] = MatchFinder.find_all(context["atu"].children, find).to_list()[0]
    assert context['result']

@given("a sequence of descendant nodes of that node")
def step_impl(context):
    assert context['result'].nodes[0].children


@when(parsers.parse("that node is replaced by '{replacement}'"))
def step_impl(context, replacement):
        context['replacement'] = replacement
        context['rewriter'] = ASTRewriter(context['atu'])
        context['rewriter'].replace(replacement, context['result'].nodes)


@when("rewrites replace is performed on that sequence of descendant nodes")
def step_impl(context):
    context['rewriter'].apply()

@then("in the modified source file that node is replaced by the given text")
def step_impl(context):
    assert context['replacement'] in context['rewriter'].apply_to_string()


@then("all rewrites on that sequence of descendant nodes are not performed or hidden")
def step_impl(context):
    assert context['rewriter'].has_changed()
