import pytest
from pytest_bdd import given, when, then, scenario, parsers
from impl import PythonASTNode, ClangASTNode, PythonPatternFactory
from syntax_tree import ASTFactory, ASTFinder, ASTRewriter, MatchFinder


@pytest.fixture
def context():
    return {
            }
@scenario('../refactor-python-file.feature','python code')
def test_refactor_python_file():
    pass

@given("'python' programming language")
def init_language_factory(context):
    # match language:
    #     case 'python': node = PythonASTNode
    #     case _: node = ClangASTNode

    context["factory"] = ASTFactory(PythonASTNode, '')


@given(parsers.parse("'{file}' file written in that programming language"))
def step_impl(context, file):
    context["atu"] = context["factory"].create(file)

@given("an AST extracted from that source file without errors")
def step_impl(context):
    assert not context["atu"].translation_unit.check_diagnostics()


@given("node 'some_old_fun' exits within that AST")
def step_impl(context):
    pattern_factory = PythonPatternFactory(context['factory'], context['atu'])
    old = pattern_factory.create_statements('a=1')
    context['result'] = MatchFinder.find_all(context["atu"].children, old).to_list()
    assert context['result']

@given("a sequence of descendant nodes of that node")
def step_impl(context):
    assert context['result'][0].nodes[0].children


@when("that node is replaced by 'def my_awesome_fun(): pass'")
def step_impl(context):
        context['rewriter'] = ASTRewriter(context['atu'])

        context['rewriter'].replace('a=5', context['result'][0].nodes)


@when("rewrites replace is performed on that sequence of descendant nodes")
def step_impl(context):
    context['rewriter'].apply()

@then("in the modified source file that node is replaced by the given text")
def step_impl(context):
    'a=5' in context['rewriter'].apply_to_string()


@then("all rewrites on that sequence of descendant nodes are not performed or hidden")
def step_impl(context):
    assert context['rewriter'].has_changed()
